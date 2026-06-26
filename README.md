# Burger API

Tracks burger contributions by user. Stores a global total and per-user counts in DynamoDB.

## Base URL

```
https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod
```

---

## Endpoints

### GET /burger

Returns the global burger count.

**Auth:** None

**Response `200`**
```json
{
  "id": "burgers",
  "count": 42,
  "last_updated": "2026-06-26T23:00:00.000000+00:00"
}
```

Returns `count: 0` and `last_updated: null` if no burgers have been added yet.

---

### POST /burger

Adds burgers for a user. Updates both the global total and that user's individual count.

**Auth:** API key required — pass as `x-api-key` header

**Request body**
```json
{
  "username": "sarah",
  "count": 3
}
```

| Field      | Type   | Required | Notes                    |
|------------|--------|----------|--------------------------|
| `username` | string | yes      | Non-empty string         |
| `count`    | number | yes      | Positive integer (≥ 1)   |

**Response `200`** — returns the updated global total
```json
{
  "id": "burgers",
  "count": 45,
  "last_updated": "2026-06-26T23:05:00.000000+00:00"
}
```

**Error responses**

| Status | Reason |
|--------|--------|
| `400`  | Missing or invalid `username` or `count` |
| `403`  | Missing or invalid API key |
| `500`  | DynamoDB error |

---

## Example requests

```bash
# Get total
curl https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/burger

# Add burgers
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/burger \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your-api-key>" \
  -d '{"username": "sarah", "count": 3}'
```

---

## Local development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Start local API (requires Docker)
DOCKER_HOST=unix://$HOME/.docker/run/docker.sock sam local start-api --env-vars env.json
```

## Deploy

```bash
sam build && sam deploy
```

---

## DynamoDB schema

Single table (`burger-counter`), two item types:

| Item | `id` | `count` | `last_updated` | `username` |
|------|------|---------|----------------|------------|
| Global total | `"burgers"` | number | ISO 8601 string | — |
| Per-user | `"user#<username>"` | number | ISO 8601 string | string |
