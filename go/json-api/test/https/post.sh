#!/usr/bin/env bash
curl --silent -X POST https://localhost:8443/users \
     -H "Content-Type: application/json" \
     -d '{"name":"John Doe","email":"john@example.com"}'
