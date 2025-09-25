# Tunnel Checklist – Cloudflare Tunnel for Bloomberg Data Broker

## Overview
Use Cloudflare Tunnel (cloudflared) to expose the Bloomberg Data Broker over HTTPS with a permanent hostname.

## Prerequisites
- Bloomberg Data Broker (`main.py`) runs on `http://localhost:8000`
- Cloudflare account with your domain onboarded (nameservers pointing to Cloudflare)
- `cloudflared.exe` available in the repository

## Step 1 – Log in cloudflared
```powershell
cloudflared.exe tunnel login
```
Approve the browser prompt so Cloudflare issues a certificate in `%USERPROFILE%\.cloudflared`.

## Step 2 – Create the tunnel
```powershell
cloudflared.exe tunnel create bloomberg-broker
```
Note the credentials file path that is printed (e.g., `C:\Users\user\.cloudflared\<uuid>.json`).

## Step 3 – Configure DNS
```powershell
cloudflared.exe tunnel route dns bloomberg-broker broker.your-domain.com
```
(or edit the CNAME in the Cloudflare dashboard to point to `<tunnel-id>.cfargotunnel.com`).

## Step 4 – Create config file
Create `cloudflared-broker.yml` (for example in `Documents`):
```yaml
tunnel: bloomberg-broker
credentials-file: C:\Users\user\.cloudflared\<uuid>.json
ingress:
  - hostname: broker.your-domain.com
    service: http://localhost:8000
  - service: http_status:404
```

## Step 5 – Start the tunnel
- Manual run:
  ```powershell
  cloudflared.exe tunnel --config "C:\Users\user\Documents\cloudflared-broker.yml" run bloomberg-broker
  ```
- Or double-click `start_cloudflared.bat`, which wraps the command.

## Step 6 – Verify
Visit `https://broker.your-domain.com/blp/fields?limit=1` (with the `x-api-key` header). You should see the expected JSON or an authentication response.

## Step 7 – Update API Schema / GPT Config
Set the server URL to `https://broker.your-domain.com` in `Production Data/Schema.yaml` and in your ChatGPT Custom GPT configuration.

## Notes
- Keep the PowerShell / batch window running while you need the tunnel.
- Optionally install cloudflared as a Windows service: `cloudflared.exe service install --config <path> --name cloudflared-broker`.
- Stop the tunnel with `Ctrl+C` or `taskkill /IM cloudflared.exe`.

## Troubleshooting
- Run `tasklist | findstr cloudflared.exe` to confirm the tunnel process.
- Ensure the credentials JSON path in the config matches the value printed in Step 2.
- DNS changes can take a few minutes to propagate—verify the CNAME in the Cloudflare dashboard if the hostname does not resolve.
