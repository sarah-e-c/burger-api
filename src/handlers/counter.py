import json
import os
from datetime import datetime, timezone

import boto3

from utils.response import ok, bad_request, server_error

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

COUNTER_KEY = "burgers"


def get_handler(event, context):
    try:
        result = table.get_item(Key={"id": COUNTER_KEY})
        item = result.get("Item", {"id": COUNTER_KEY, "count": 0, "last_updated": None})
        return ok(item)
    except Exception as e:
        return server_error(str(e))


def increment_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return bad_request("Invalid JSON body")

    username = body.get("username", "").strip() if isinstance(body.get("username"), str) else ""
    if not username:
        return bad_request("'username' is required")

    count = body.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        return bad_request("'count' must be a positive integer")

    now = datetime.now(timezone.utc).isoformat()
    update_expr = "SET #c = if_not_exists(#c, :zero) + :n, last_updated = :ts"
    attr_names = {"#c": "count"}

    try:
        table.update_item(
            Key={"id": COUNTER_KEY},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues={":n": count, ":zero": 0, ":ts": now},
        )
        table.update_item(
            Key={"id": f"user#{username}"},
            UpdateExpression=update_expr + ", username = :u",
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues={":n": count, ":zero": 0, ":ts": now, ":u": username},
        )
        global_item = table.get_item(Key={"id": COUNTER_KEY})["Item"]
        return ok(global_item)
    except Exception as e:
        return server_error(str(e))
