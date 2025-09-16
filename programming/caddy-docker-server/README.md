# Python Server with Caddy Reverse Proxy

A simple FastAPI server containerized with Docker and served through Caddy reverse proxy.

## Development Setup

1. Build and start the containers:
```bash
docker compose -f compose-dev.yml up -d --build
```

2. Access the application at `http://localhost:8080`

## Production Setup (HTTPS)

For production deployment with HTTPS on `example.com`:

1. Ensure your domain points to the server
2. Build and start the production containers:
```bash
docker compose -f compose-prod.yml up -d --build
```

3. The application will be available at `https://example.com`

Caddy will automatically handle:
- SSL certificate generation via Let's Encrypt
- HTTP to HTTPS redirect
- Certificate renewal

## Teardown

**Development:**
```bash
docker compose -f compose-dev.yml down
# With volumes:
docker compose -f compose-dev.yml down -v
```

**Production:**
```bash
docker compose -f compose-prod.yml down
# With volumes (removes SSL certificates):
docker compose -f compose-prod.yml down -v
```

## Endpoints

- `/` - Returns a "Hello World" message
- `/health` - Health check endpoint

## Architecture

- **Python Server**: FastAPI application running on uvicorn (port 8000)
- **Caddy**: Reverse proxy serving on port 8080, forwarding to the Python server
- **Docker**: Containerized setup with docker compose for easy deployment

## Files

- `main.py` - FastAPI application
- `pyproject.toml` - Python dependencies and project metadata
- `Dockerfile` - Container configuration for Python server
- `compose-dev.yml` - Development multi-container setup
- `compose-prod.yml` - Production multi-container setup with HTTPS
- `dev.Caddyfile` - Development Caddy configuration (HTTP)
- `prod.Caddyfile` - Production Caddy configuration (HTTPS with example.com)
