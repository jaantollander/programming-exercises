# Static Site with Caddy

A simple static website served by Caddy web server using Docker and Docker Compose. This project demonstrates how to containerize a static site with Caddy as the web server.

## Quick Start

### Development
```bash
docker compose up
```

Visit [http://localhost:8080](http://localhost:8080)

### Production
```bash
docker compose -f docker-compose-prod.yml up
```

## Project Structure

- `index.html` - Static HTML page
- `Dockerfile` - Custom Caddy container image
- `docker compose.yml` - Development configuration (localhost:8080)
- `docker compose-prod.yml` - Production configuration with SSL support
- `README.md` - This documentation

## Configuration Details

### Development Setup
- Serves on port 8080
- Uses localhost domain
- Built from custom Dockerfile

### Production Setup
- Serves on ports 80 (HTTP) and 443 (HTTPS)
- Configured for example.com domain
- Includes persistent volumes for Caddy data and config
- Automatic SSL/TLS certificates

## Requirements

- Docker
- Docker Compose

## Commands

Build and start containers:
```bash
docker compose up --build
```

Run in background:
```bash
docker compose up -d
```

Stop containers:
```bash
docker compose down
```
