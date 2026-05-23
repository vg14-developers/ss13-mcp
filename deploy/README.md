# Deploy runbook (Oracle Free Tier ARM Ampere)

## One-time provisioning

1. Create an Oracle Cloud "Always Free" ARM Ampere instance:
   - Shape: VM.Standard.A1.Flex
   - 4 OCPUs, 24 GB RAM
   - Image: Canonical Ubuntu 22.04 (ARM)
   - Open ports 22, 80, 443 in the VCN security list and instance firewall.

2. SSH in and install Docker:
   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER && newgrp docker
   ```

3. Create the deploy directory and copy these files (the deploy.yml workflow
   does this automatically once configured; do it by hand for first install):
   ```bash
   sudo mkdir -p /opt/vgstation13-mcp
   sudo chown $USER:$USER /opt/vgstation13-mcp
   cd /opt/vgstation13-mcp
   # scp docker-compose.yml Caddyfile and the systemd/ folder from this repo
   cp .env.example .env
   $EDITOR .env
   sudo mkdir -p /var/cache/vgstation13-mcp/conversions
   sudo chown -R 1000:1000 /var/cache/vgstation13-mcp
   ```

4. Register a GitHub OAuth App at
   https://github.com/organizations/vg14-developers/settings/applications/new
   - Homepage URL: `https://<your-domain>/`
   - Callback URL: `https://<your-domain>/oauth/callback`
   - Paste client ID and secret into `.env`.

5. Generate session secret: `openssl rand -hex 32` → into `.env`.

6. Install the systemd unit:
   ```bash
   sudo cp systemd/vgstation13-mcp.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now vgstation13-mcp
   ```

7. Verify:
   ```bash
   curl -H "Authorization: Bearer <a-real-gh-token>" https://<your-domain>/health
   ```
   Expect HTTP 200 with `{"status":"ok","user":"<your-login>"}`.

8. Configure an uptime monitor. The `/health` endpoint requires auth, so either:
   - Provision a long-lived monitor-only GitHub PAT and pass it as a Bearer
     header (UptimeRobot Pro / BetterStack support custom headers), OR
   - Treat HTTP 401 as "alive" — getting any structured response means the
     server is up. Free-tier UptimeRobot can be configured to treat 401 as up.

## Rotating the OAuth client secret

1. Regenerate at the GitHub OAuth App settings page.
2. Update `/opt/vgstation13-mcp/.env`.
3. `sudo systemctl restart vgstation13-mcp`.

## Rolling back a bad snapshot

```bash
cd /opt/vgstation13-mcp
docker compose down
docker pull ghcr.io/vg14-developers/vgstation13-mcp:vg13-<old-short-sha>
docker tag ghcr.io/vg14-developers/vgstation13-mcp:vg13-<old-short-sha> \
           ghcr.io/vg14-developers/vgstation13-mcp:latest
docker compose up -d
```

## Reclamation recovery

If Oracle reclaims the instance: provision a new one following steps 1–8.
DNS update plus reattaching the block volume that holds
`/var/cache/vgstation13-mcp` is the only state worth preserving; everything
else rebuilds from `:latest`.
