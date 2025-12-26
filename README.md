# Fetal MRI Reconstruction

A Docker-based implementation of the NeSVoR super-resolution reconstruction pipeline for clinical use. Includes a **web application** for easy use by clinicians - just upload, click, and download.

## Features

- **Web Interface**: Simple browser-based UI for non-technical users
- **Automatic Processing**: Brain masking, preprocessing, and 3D reconstruction
- **Preview & Download**: View results in 2D/3D before downloading
- **Secure Remote Access**: Optional Cloudflare Tunnel setup for access from anywhere
- **Automatic Backup**: Optional backup of results to external storage

---

## Quick Start (Web Application)

### Windows

1. **Install Docker Desktop** with WSL2: https://docker.com/products/docker-desktop

2. **Clone and start**:
   ```powershell
   git clone https://github.com/GerardMJuan/clinic-nesvor-docker
   cd clinic-nesvor-docker

   # Double-click to start:
   scripts\start-server.bat
   ```

3. **Open** http://localhost:8501 in your browser

### Linux

```bash
git clone https://github.com/GerardMJuan/clinic-nesvor-docker
cd clinic-nesvor-docker
docker-compose -f docker-compose.webapp.yml up -d

# Open http://localhost:8501
```

---

## Web Application Usage

1. **Upload** your MRI stacks (.nii.gz files)
2. **Click** "Start Reconstruction"
3. **Wait** for processing (5-15 minutes)
4. **Preview** the result in 2D/3D
5. **Download** the reconstruction

![Web App Screenshot](docs/screenshot.png)

---

## Remote Access (Optional)

To access the app from outside your network (e.g., from a hospital):

```powershell
# Windows
.\scripts\setup-tunnel.ps1

# Linux
./scripts/setup-tunnel.sh
```

This sets up a secure tunnel with:
- Your own domain (e.g., `mri.yourclinic.com`)
- Login protection (email verification)
- HTTPS encryption
- Free (Cloudflare free tier)

See [docs/REMOTE_ACCESS_SETUP.md](docs/REMOTE_ACCESS_SETUP.md) for details.

---

## Backup (Optional)

Enable automatic backup of reconstruction results:

1. Edit `docker-compose.webapp.yml`:
   ```yaml
   volumes:
     - /path/to/backup/folder:/app/data/backups
   environment:
     - BACKUP_ENABLED=true
   ```

2. Restart the server

Results are backed up to `YYYY-MM-DD/sessionid_recon.nii.gz`.

---

## Command Line Usage (Alternative)

For batch processing or scripting:

```bash
# Build the Docker image
docker build -t docker-nesvor-clinic .

# Run reconstruction
docker run --gpus all \
  -v /path/to/input:/app/data/inputs \
  -v /path/to/output:/app/data/outputs \
  docker-nesvor-clinic
```

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | NVIDIA 6GB VRAM | NVIDIA 8GB+ VRAM |
| RAM | 16 GB | 32 GB |
| Storage | 50 GB free | SSD recommended |

Tested on: RTX 3060 Ti (8GB), RTX 3090, A100

---

## Output Structure

```
output/
├── masks/           # Brain masks for each input stack
├── preproc/         # Preprocessed (cropped, masked) images
├── recon.nii.gz     # Final 3D reconstruction (0.8mm isotropic)
└── recon.pt         # Neural network model (optional)
```

---

## Configuration

Default parameters (adjustable in web UI):

| Parameter | Default | Description |
|-----------|---------|-------------|
| Resolution | 0.8 mm | Output isotropic voxel size |
| Bias correction | Enabled | N4 bias field correction |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/start-server.bat` | Start web app (Windows) |
| `scripts/stop-server.bat` | Stop web app (Windows) |
| `scripts/setup-tunnel.ps1` | Setup remote access (Windows) |
| `scripts/setup-tunnel.sh` | Setup remote access (Linux) |

---

## Troubleshooting

**"GPU not available"**
- Ensure NVIDIA drivers are installed
- Ensure Docker has GPU access: `docker run --gpus all nvidia/cuda:11.0-base nvidia-smi`

**"Connection refused"**
- Check Docker is running: `docker ps`
- Check the container: `docker-compose -f docker-compose.webapp.yml logs`

**Slow reconstruction**
- Normal processing time: 5-15 minutes
- Ensure GPU is being used (check nvidia-smi during processing)

---

## License

Built upon [NeSVoR](https://github.com/daviddmc/NeSVoR). Please see their license for terms of use.

## Citation

If you use this pipeline in your research, please cite:

> Ebner, M., Wang, G., Li, W., et al. (2020). An automated framework for localization, segmentation and super-resolution reconstruction of fetal brain MRI. NeuroImage, 206, 116324.
