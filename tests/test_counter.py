import json
import os
import sys

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TABLE_NAME = "test-counter"


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)


@pytest.fixture
def ddb_table():
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        table = ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


def _post(body):
    return {"body": json.dumps(body)}


def test_get_counter_returns_zero_when_empty(ddb_table):
    from handlers.counter import get_handler
    resp = get_handler({}, {})
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])
    assert data["count"] == 0
    assert data["last_updated"] is None


def test_increment_creates_counter(ddb_table):
    from handlers.counter import increment_handler
    resp = increment_handler(_post({"username": "sarah", "count": 1}), {})
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])
    assert data["count"] == 1
    assert data["last_updated"] is not None


def test_increment_is_cumulative(ddb_table):
    from handlers.counter import increment_handler
    increment_handler(_post({"username": "sarah", "count": 1}), {})
    increment_handler(_post({"username": "sarah", "count": 1}), {})
    resp = increment_handler(_post({"username": "sarah", "count": 1}), {})
    data = json.loads(resp["body"])
    assert data["count"] == 3


def test_get_reflects_increments(ddb_table):
    from handlers.counter import increment_handler, get_handler
    increment_handler(_post({"username": "sarah", "count": 2}), {})
    increment_handler(_post({"username": "bob", "count": 3}), {})
    resp = get_handler({}, {})
    data = json.loads(resp["body"])
    assert data["count"] == 5


def test_increment_adds_user_item(ddb_table):
    from handlers.counter import increment_handler
    increment_handler(_post({"username": "sarah", "count": 4}), {})
    item = ddb_table.get_item(Key={"id": "user#sarah"})["Item"]
    assert item["username"] == "sarah"
    assert item["count"] == 4


def test_increment_accumulates_per_user(ddb_table):
    from handlers.counter import increment_handler
    increment_handler(_post({"username": "sarah", "count": 2}), {})
    increment_handler(_post({"username": "sarah", "count": 3}), {})
    item = ddb_table.get_item(Key={"id": "user#sarah"})["Item"]
    assert item["count"] == 5


def test_multiple_users_tracked_separately(ddb_table):
    from handlers.counter import increment_handler
    increment_handler(_post({"username": "sarah", "count": 5}), {})
    increment_handler(_post({"username": "bob", "count": 2}), {})
    sarah = ddb_table.get_item(Key={"id": "user#sarah"})["Item"]
    bob = ddb_table.get_item(Key={"id": "user#bob"})["Item"]
    assert sarah["count"] == 5
    assert bob["count"] == 2


def test_increment_missing_username_returns_400(ddb_table):
    from handlers.counter import increment_handler
    resp = increment_handler(_post({"count": 1}), {})
    assert resp["statusCode"] == 400


def test_increment_invalid_count_returns_400(ddb_table):
    from handlers.counter import increment_handler
    for bad_count in [None, 0, -1, "three", 1.5, True]:
        resp = increment_handler(_post({"username": "sarah", "count": bad_count}), {})
        assert resp["statusCode"] == 400, f"expected 400 for count={bad_count!r}"
