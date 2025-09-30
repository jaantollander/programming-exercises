```bash
docker compose -f compose.yml up -d --build
```

```bash
docker cp caddy-self-signed:/data/caddy/pki/authorities/local/root.crt root.crt
```

```bash
curl --cacert root.crt https://localhost:8443
```

```bash
docker compose -f compose.yml down
```
