# Secure Remote Access Setup Guide

This guide sets up secure remote access to the Fetal MRI Reconstruction web app from your home PC using Cloudflare Tunnel.

## What You Get

| Feature | Details |
|---------|---------|
| **Custom domain** | `mri.yourclinic.com` (or any domain you own) |
| **Permanent URL** | Same URL always, as long as tunnel runs |
| **Login required** | Email-based one-time codes or Google/GitHub login |
| **HTTPS** | Automatic SSL, encrypted traffic |
| **Cost** | **Free** (Cloudflare free tier) |

---

## Prerequisites

1. A domain name you own (e.g., `yourclinic.com`)
   - If you don't have one: ~$10-15/year from Namecheap, Porkbun, or Google Domains
2. Free Cloudflare account: https://dash.cloudflare.com/sign-up
3. Docker installed on your PC

---

## Step 1: Add Your Domain to Cloudflare (One-time, 10 min)

1. Log into [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **"Add a Site"** → Enter your domain
3. Select **Free plan**
4. Cloudflare will show you nameservers (e.g., `anna.ns.cloudflare.com`)
5. Go to your domain registrar and change nameservers to Cloudflare's
6. Wait for DNS propagation (usually 5-30 minutes)

---

## Step 2: Install Cloudflared

### Windows (PowerShell as Administrator)
```powershell
# Option 1: winget
winget install Cloudflare.cloudflared

# Option 2: Download directly
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "C:\Program Files\cloudflared\cloudflared.exe"
```

### Linux
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

---

## Step 3: Create a Permanent Tunnel (One-time)

```bash
# 1. Login to Cloudflare (opens browser)
cloudflared tunnel login

# 2. Create a named tunnel
cloudflared tunnel create fetal-mri

# This creates a tunnel with a permanent ID like:
# Created tunnel fetal-mri with id a]b1c2d3-e4f5-6789-abcd-ef0123456789
# Save this ID!
```

---

## Step 4: Configure the Tunnel

Create a config file:

### Windows: `C:\Users\YourName\.cloudflared\config.yml`
### Linux: `~/.cloudflared/config.yml`

```yaml
# Cloudflare Tunnel Configuration
tunnel: YOUR_TUNNEL_ID  # Replace with your tunnel ID from Step 3
credentials-file: /path/to/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  # Your custom subdomain
  - hostname: mri.yourclinic.com  # Replace with your domain
    service: http://localhost:8501

  # Catch-all (required)
  - service: http_status:404
```

**Windows path example:**
```yaml
credentials-file: C:\Users\YourName\.cloudflared\YOUR_TUNNEL_ID.json
```

---

## Step 5: Add DNS Record

```bash
# This creates mri.yourclinic.com pointing to your tunnel
cloudflared tunnel route dns fetal-mri mri.yourclinic.com
```

Or manually in Cloudflare Dashboard:
1. Go to DNS settings for your domain
2. Add CNAME record:
   - Name: `mri`
   - Target: `YOUR_TUNNEL_ID.cfargotunnel.com`
   - Proxy: Yes (orange cloud)

---

## Step 6: Add Login Protection (Cloudflare Access)

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com)
2. Navigate to **Access** → **Applications** → **Add an Application**
3. Select **Self-hosted**
4. Configure:
   - **Application name**: Fetal MRI Reconstruction
   - **Session duration**: 24 hours (or your preference)
   - **Application domain**: `mri.yourclinic.com`

5. Create a **Policy**:
   - **Policy name**: Allowed Users
   - **Action**: Allow
   - **Include rules** (choose one or more):

   **Option A: Specific emails**
   - Selector: `Emails`
   - Value: `doctor@yourclinic.com, radiologist@yourclinic.com`

   **Option B: Email domain (anyone @yourclinic.com)**
   - Selector: `Email domain`
   - Value: `yourclinic.com`

   **Option C: One-time PIN to any email**
   - Selector: `Emails`
   - Value: `*` (or specific emails)
   - Authentication: One-time PIN

6. Save the application

---

## Step 7: Run Everything

### Start the Web App
```bash
docker-compose -f docker-compose.webapp.yml up -d
```

### Start the Tunnel
```bash
# Run in foreground (for testing)
cloudflared tunnel run fetal-mri

# Or run as a service (persistent)
# Windows:
cloudflared service install
net start cloudflared

# Linux:
sudo cloudflared service install
sudo systemctl start cloudflared
```

---

## Step 8: Test It

1. Open `https://mri.yourclinic.com` from any device
2. You'll see Cloudflare Access login page
3. Enter your email → receive one-time code → access granted
4. Use the app!

---

## Auto-Start on Boot

### Windows (Task Scheduler)

Create `start-fetal-mri.bat`:
```batch
@echo off
cd C:\path\to\clinic-nesvor-docker
docker-compose -f docker-compose.webapp.yml up -d
cloudflared tunnel run fetal-mri
```

Add to Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task → "Fetal MRI Server"
3. Trigger: "When the computer starts"
4. Action: Start a program → select your .bat file
5. Check "Run with highest privileges"

### Linux (systemd)

The `cloudflared service install` command already creates a systemd service.

For Docker:
```bash
# Docker Compose handles restart automatically with:
# restart: unless-stopped
```

---

## Quick Reference

| What | Command |
|------|---------|
| Start web app | `docker-compose -f docker-compose.webapp.yml up -d` |
| Stop web app | `docker-compose -f docker-compose.webapp.yml down` |
| Start tunnel | `cloudflared tunnel run fetal-mri` |
| Check tunnel status | `cloudflared tunnel info fetal-mri` |
| View logs | `docker-compose -f docker-compose.webapp.yml logs -f` |

---

## Security Summary

| Layer | Protection |
|-------|------------|
| **Transport** | HTTPS (TLS 1.3) - automatic |
| **Network** | No open ports on your PC - Cloudflare connects outbound |
| **Authentication** | Cloudflare Access - email verification |
| **DDoS** | Cloudflare's DDoS protection (free) |
| **Access logs** | Who accessed, when - in Cloudflare dashboard |

---

## Troubleshooting

**"Tunnel not found"**
```bash
cloudflared tunnel list  # Check tunnel exists
```

**"Connection refused"**
```bash
# Make sure web app is running
docker ps  # Should show fetal-mri-reconstruction container
```

**"Access denied"**
- Check your email is in the Cloudflare Access policy
- Check you're using the right domain

**Tunnel disconnects**
- Install as a service (Step 7) for automatic reconnection
