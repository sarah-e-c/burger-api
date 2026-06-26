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


def test_get_counter_returns_zero_when_empty(ddb_table):
    from handlers.counter import get_handler
    resp = get_handler({}, {})
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])
    assert data["count"] == 0
    assert data["last_updated"] is None


def test_increment_creates_counter(ddb_table):
    from handlers.counter import increment_handler
    resp = increment_handler({}, {})
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])
    assert data["count"] == 1
    assert data["last_updated"] is not None


def test_increment_is_cumulative(ddb_table):
    from handlers.counter import increment_handler
    increment_handler({}, {})
    increment_handler({}, {})
    resp = increment_handler({}, {})
    data = json.loads(resp["body"])
    assert data["count"] == 3


def test_get_reflects_increments(ddb_table):
    from handlers.counter import increment_handler, get_handler
    increment_handler({}, {})
    increment_handler({}, {})
    resp = get_handler({}, {})
    data = json.loads(resp["body"])
    assert data["count"] == 2
