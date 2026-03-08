# Deployment and Production

This document covers running CloudRadar in production, Docker, and security considerations.

## Quick run (single machine)

1. **Install**

   ```bash
   pip install -e .
   cd frontend && npm install && npm run build
   ```

2. **Run** (from project root)

   ```bash
   python -m cspm.cli ui --host 0.0.0.0 --port 8000
   ```

   Open `http://<host>:8000`. The server serves the Vue app and the API.

## Docker

A minimal Dockerfile is provided. Build and run:

```bash
docker build -t cloud-cspm .
docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml -v $(pwd)/snapshots:/app/snapshots cloud-cspm ui --host 0.0.0.0 --port 8000
```

**Notes:**

- The image does not include the built Vue frontend by default. For a full deployment, either:
  - Build the frontend before `docker build` and ensure `frontend/dist` is copied, or
  - Use a multi-stage build that runs `npm run build` in the image.
- Mount `config.yaml` and `snapshots` (or use env vars and a volume) so state and snapshots persist.
- Do not bake credentials into the image; use env vars or a mounted config.

## Environment for production

- **Credentials:** Prefer IAM roles (AWS), workload identity (GCP), or managed identity (Azure) over keys in config. If you use `config.yaml`, restrict permissions (`chmod 600`) and keep it off version control.
- **Host:** Use `--host 0.0.0.0` only if the process is behind a reverse proxy or firewall. Prefer binding to a private IP when possible.
- **HTTPS:** Run behind a reverse proxy (e.g. Nginx, Caddy, Traefik) with TLS. The app does not terminate TLS.
- **Secrets:** For production, consider loading credentials from a secret manager (e.g. AWS Secrets Manager, Vault) and writing env or a temporary config instead of storing secrets in a long-lived `config.yaml`.

## Reverse proxy example (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name cspm.example.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    location /api/jobs/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        chunked_transfer_encoding off;
    }
}
```

The `/api/jobs/` block disables buffering for SSE (scan progress).

## Process management

- Use a process manager (systemd, supervisord, or a container orchestrator) to keep the UI process running and restart on failure.
- Optional: run the CLI in cron for scheduled scans and use the UI only for ad-hoc runs and viewing.

## Backup

- **Snapshots:** Back up the `snapshots/` directory (or equivalent) if you need scan history.
- **Config:** If you persist credentials in `config.yaml`, include it in backup only if stored securely.
