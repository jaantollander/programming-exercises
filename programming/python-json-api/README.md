# Simple JSON API

A FastAPI application with OpenID Connect (OIDC) and JWT authentication.

## Installation

Install virtual environment

```shell
uv venv --python 3.10 .venv
```

Install the project

```shell
uv pip install -e . .[dev]
```

## Running the API

```shell
python main.py
```

The API will be available at `http://localhost:8000`

## API Usage Examples

Requires `curl` and `jq` tools.

### 1. Register a new user
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123"
  }'
```

### 2. Login and get access token
```bash
# Login and save token to variable
TOKEN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 3. Get current user info
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Create an item
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "Gaming laptop",
    "price": 1299.99
  }'
```

### 5. Get all user's items
```bash
curl -X GET "http://localhost:8000/items" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Update an item
```bash
curl -X PUT "http://localhost:8000/items/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop",
    "description": "High-end gaming laptop",
    "price": 1599.99
  }'
```

### 7. Delete an item
```bash
curl -X DELETE "http://localhost:8000/items/1" \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Check OIDC configuration
```bash
curl -X GET "http://localhost:8000/auth/oidc/config"
```

## Complete Example Script

```bash
#!/bin/bash
BASE_URL="http://localhost:8000"

# Register user
echo "Registering user..."
curl -s -X POST "$BASE_URL/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Login and get token
echo -e "\n\nLogging in..."
TOKEN=$(curl -s -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}' | jq -r '.access_token')

# Create item
echo -e "\n\nCreating item..."
curl -s -X POST "$BASE_URL/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "A test item", "price": 29.99}' | jq

# Get items
echo -e "\n\nGetting items..."
curl -s -X GET "$BASE_URL/items" \
  -H "Authorization: Bearer $TOKEN" | jq
```
