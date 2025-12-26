# Cloudflare Tunnel Setup Script for Windows
# Run this in PowerShell as Administrator

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fetal MRI - Cloudflare Tunnel Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared is installed
$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "Installing cloudflared..." -ForegroundColor Yellow
    winget install Cloudflare.cloudflared
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "✓ cloudflared installed" -ForegroundColor Green
} else {
    Write-Host "✓ cloudflared already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 1: Login to Cloudflare" -ForegroundColor Yellow
Write-Host "---------------------------"
Write-Host "This will open a browser window. Log in and authorize."
Read-Host "Press Enter to continue"
cloudflared tunnel login
Write-Host "✓ Logged in" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Create Tunnel" -ForegroundColor Yellow
Write-Host "---------------------"
$TunnelName = Read-Host "Enter a name for your tunnel (default: fetal-mri)"
if ([string]::IsNullOrEmpty($TunnelName)) { $TunnelName = "fetal-mri" }

# Check if tunnel exists
$existingTunnel = cloudflared tunnel list | Select-String $TunnelName
if ($existingTunnel) {
    Write-Host "Tunnel '$TunnelName' already exists"
    $TunnelId = ($existingTunnel -split '\s+')[0]
} else {
    cloudflared tunnel create $TunnelName
    $tunnelList = cloudflared tunnel list | Select-String $TunnelName
    $TunnelId = ($tunnelList -split '\s+')[0]
}
Write-Host "✓ Tunnel ID: $TunnelId" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Configure Domain" -ForegroundColor Yellow
Write-Host "------------------------"
$Domain = Read-Host "Enter your full domain (e.g., mri.yourclinic.com)"

# Create config directory
$ConfigDir = "$env:USERPROFILE\.cloudflared"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir | Out-Null
}

# Create config file
$ConfigContent = @"
tunnel: $TunnelId
credentials-file: $ConfigDir\$TunnelId.json

ingress:
  - hostname: $Domain
    service: http://localhost:8501
  - service: http_status:404
"@

$ConfigContent | Out-File -FilePath "$ConfigDir\config.yml" -Encoding UTF8
Write-Host "✓ Config created at $ConfigDir\config.yml" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Create DNS Record" -ForegroundColor Yellow
Write-Host "-------------------------"
Write-Host "Adding DNS record for $Domain..."
try {
    cloudflared tunnel route dns $TunnelName $Domain
    Write-Host "✓ DNS record created" -ForegroundColor Green
} catch {
    Write-Host "Note: DNS record may already exist or domain not in Cloudflare" -ForegroundColor Yellow
    Write-Host "You may need to add it manually in Cloudflare Dashboard"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start the web app:"
Write-Host "   docker-compose -f docker-compose.webapp.yml up -d" -ForegroundColor White
Write-Host ""
Write-Host "2. Start the tunnel:"
Write-Host "   cloudflared tunnel run $TunnelName" -ForegroundColor White
Write-Host ""
Write-Host "3. (Optional) Install as Windows service for auto-start:"
Write-Host "   cloudflared service install" -ForegroundColor White
Write-Host "   Start-Service cloudflared" -ForegroundColor White
Write-Host ""
Write-Host "4. Add login protection:" -ForegroundColor Yellow
Write-Host "   - Go to: https://one.dash.cloudflare.com"
Write-Host "   - Navigate to: Access -> Applications -> Add Application"
Write-Host "   - Add your domain: $Domain"
Write-Host "   - Create a policy with allowed email addresses"
Write-Host ""
Write-Host "Your app will be available at: https://$Domain" -ForegroundColor Green
Write-Host ""

# Create a startup batch file
$StartupScript = @"
@echo off
echo Starting Fetal MRI Reconstruction Server...
cd /d $PSScriptRoot\..
docker-compose -f docker-compose.webapp.yml up -d
cloudflared tunnel run $TunnelName
"@

$StartupScript | Out-File -FilePath "$PSScriptRoot\start-server.bat" -Encoding ASCII
Write-Host "Created start-server.bat for easy startup" -ForegroundColor Green
