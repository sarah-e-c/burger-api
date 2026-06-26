import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def _resp(status: int, body) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def ok(data):
    return _resp(200, data)


def created(data):
    return _resp(201, data)


def bad_request(message: str):
    return _resp(400, {"error": message})


def not_found(message: str):
    return _resp(404, {"error": message})


def server_error(message: str):
    return _resp(500, {"error": message})
