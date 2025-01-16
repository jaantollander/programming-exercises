#!/usr/bin/env bash

# Build the application container
docker build --tag localhost/myapp:latest --file app.dockerfile .

# Run the application
docker compose up -d

# Set up local ca certificates
# https://caddyserver.com/docs/running#local-https-with-docker
if [ ! -f /usr/local/share/ca-certificates/root.crt  ]; then
    _TMPFILE=$(mktemp --suffix .crt)
    docker compose cp caddy:/data/caddy/pki/authorities/local/root.crt "$_TMPFILE"
    sudo cp "$_TMPFILE" /usr/local/share/ca-certificates/root.crt
    sudo update-ca-certificates
    rm "$_TMPFILE"
fi
