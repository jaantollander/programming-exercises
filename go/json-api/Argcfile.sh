#!/usr/bin/env bash

set -e

# @cmd
run() {
    # Build the application container
    docker build --tag localhost/myapp:latest --file app.dockerfile .

    # Run the application
    docker compose up -d

    # Set up local ca certificates
    # https://caddyserver.com/docs/running#local-https-with-docker
    local LOCAL_CRT TMP_CRT
    LOCAL_CRT=/usr/local/share/ca-certificates/caddy-docker.crt
    if [ ! -f "$LOCAL_CRT"  ]; then
        TMP_CRT=$(mktemp --suffix .crt)
        docker compose cp caddy:/data/caddy/pki/authorities/local/root.crt "$TMP_CRT"
        sudo cp "$TMP_CRT" "$LOCAL_CRT"
        sudo chmod u=rw,go=r "$LOCAL_CRT"
        sudo update-ca-certificates
        rm "$TMP_CRT"
    fi
}

# @cmd
stop() {
    docker container stop myapp caddy
}

# See more details at https://github.com/sigoden/argc
eval "$(argc --argc-eval "$0" "$@")"
