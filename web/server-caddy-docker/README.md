# Python Server with Caddy Reverse Proxy

A simple FastAPI server containerized with Docker and served through Caddy reverse proxy.

## Setup

1. Build and start the containers:
```bash
docker-compose up --build
```

2. Access the application at `http://localhost:8080`

## Teardown

To stop and remove the containers:
```bash
docker-compose down
```

To stop and remove containers along with volumes:
```bash
docker-compose down -v
```

## Endpoints

- `/` - Returns a "Hello World" message
- `/health` - Health check endpoint

## Architecture

- **Python Server**: FastAPI application running on uvicorn (port 8000)
- **Caddy**: Reverse proxy serving on port 8080, forwarding to the Python server
- **Docker**: Containerized setup with docker-compose for easy deployment

## Files

- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration for Python server
- `docker-compose.yml` - Multi-container setup
- `Caddyfile` - Caddy reverse proxy configuration
