import os
from datetime import datetime, timezone

import boto3

from utils.response import ok, server_error

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
        result = table.update_item(
            Key={"id": COUNTER_KEY},
            UpdateExpression="SET #c = if_not_exists(#c, :zero) + :one, last_updated = :ts",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={
                ":one": 1,
                ":zero": 0,
                ":ts": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return ok(result["Attributes"])
    except Exception as e:
        return server_error(str(e))
