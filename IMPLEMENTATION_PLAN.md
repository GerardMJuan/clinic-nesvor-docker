# Fetal MRI Web Application - Implementation Plan

## Overview

Transform the NeSVoR Docker-based fetal MRI reconstruction tool into a user-friendly web application for clinicians.

### Goals
- **Simple interface**: Non-technical users can upload data and download results
- **Minimal configuration**: Smart defaults with optional advanced settings
- **Single deployment**: Streamlit app running on a GPU server
- **Progress tracking**: Real-time feedback during processing
- **7-day storage**: Results available for download for one week

---

## Architecture

### Single Streamlit Application

```
┌─────────────────────────────────────────────────────────────┐
│                    GPU Server (Docker)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Streamlit Web Application                   ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ ││
│  │  │  Frontend   │──│  Processing  │──│  NeSVoR Engine │ ││
│  │  │  (Upload,   │  │  Pipeline    │  │  (GPU)         │ ││
│  │  │  Progress,  │  │              │  │                │ ││
│  │  │  Download)  │  │              │  │                │ ││
│  │  └─────────────┘  └──────────────┘  └────────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│  ┌───────────────────────────┴───────────────────────────┐  │
│  │                    Storage (7 days)                    │  │
│  │     /app/data/sessions/{session_id}/                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Why Streamlit?**
- Python-native (integrates directly with existing NeSVoR code)
- Built-in file upload/download components
- Professional appearance with minimal CSS
- Easy Docker deployment
- No frontend JavaScript knowledge required

---

## Application Structure

```
clinic-nesvor-docker/
├── webapp/
│   ├── __init__.py
│   ├── app.py                 # Main Streamlit application
│   ├── processing.py          # Backend processing pipeline
│   ├── storage.py             # Session & file management (7-day cleanup)
│   ├── visualization.py       # 2D slice previews + NiiVue 3D viewer
│   └── config.py              # Configuration defaults
├── Dockerfile.webapp          # Web app Docker image
├── docker-compose.webapp.yml  # Docker Compose for deployment
├── requirements.webapp.txt    # Web app Python dependencies
├── prepare_recon.py           # (existing) Preprocessing script
├── run_recon.sh               # (existing) Reconstruction script
└── utils/                     # (existing) Utility functions
```

---

## User Interface Design

```
┌─────────────────────────────────────────────────────────────┐
│  Fetal Brain MRI Reconstruction                             │
│  Transform 2D MRI slices into high-resolution 3D volumes    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STEP 1: Upload MRI Stacks                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │     Drag and drop .nii.gz files here                 │  │
│  │     or click to browse                                │  │
│  │                                                       │  │
│  │     Accepted: NIfTI files (.nii.gz)                  │  │
│  │     Recommended: 3-6 stacks from different angles    │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Uploaded: stack_1.nii.gz, stack_2.nii.gz, stack_3.nii.gz  │
│                                                             │
│  ▼ Advanced Settings                                        │
│    Output resolution: [0.8] mm (lower = higher quality)    │
│    [✓] Bias field correction                               │
│                                                             │
│  [ Start Reconstruction ]                                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  STEP 2: Processing                                         │
│                                                             │
│  ████████████████░░░░░░░░ 65%                              │
│                                                             │
│  [✓] Files validated (3 stacks)                            │
│  [✓] Brain masks created                                   │
│  [✓] Images preprocessed                                   │
│  [⏳] Reconstructing 3D volume... (est. 5 min remaining)   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  STEP 3: Results                                            │
│                                                             │
│  [ Download Reconstruction ] recon.nii.gz (45 MB)          │
│                                                             │
│  Preview:                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │ Axial   │ │ Coronal │ │ Sagittal│   [ Open 3D Viewer ] │
│  │  slice  │ │  slice  │ │  slice  │                       │
│  └─────────┘ └─────────┘ └─────────┘                       │
│                                                             │
│  Results available for 7 days                              │
│  Download link: https://your-server/download/abc123        │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Main Application (`webapp/app.py`)

```python
import streamlit as st
from webapp.processing import ReconstructionPipeline
from webapp.storage import SessionManager
from webapp.visualization import display_slices, create_niivue_viewer

st.set_page_config(
    page_title="Fetal Brain MRI Reconstruction",
    page_icon="🧠",
    layout="wide"
)

def main():
    st.title("Fetal Brain MRI Reconstruction")
    st.markdown("Transform 2D MRI slices into high-resolution 3D volumes")

    # Initialize session
    session = SessionManager.get_or_create_session()

    # Step 1: File Upload
    st.header("Step 1: Upload MRI Stacks")
    uploaded_files = st.file_uploader(
        "Upload NIfTI files (.nii.gz)",
        type=["nii.gz", "nii"],
        accept_multiple_files=True,
        help="Upload 3-6 stacks from different acquisition angles"
    )

    # Advanced settings (collapsed by default)
    with st.expander("Advanced Settings"):
        resolution = st.slider("Output resolution (mm)", 0.5, 1.5, 0.8, 0.1)
        bias_correction = st.checkbox("Bias field correction", value=True)

    # Process button
    if uploaded_files and st.button("Start Reconstruction", type="primary"):
        run_pipeline(session, uploaded_files, resolution, bias_correction)

    # Show results if available
    if session.has_results():
        display_results(session)

if __name__ == "__main__":
    main()
```

### 2. Processing Pipeline (`webapp/processing.py`)

```python
import subprocess
import os
from pathlib import Path
from utils.utils import create_brain_masks, process_masks_and_images

class ReconstructionPipeline:
    """Orchestrates the full reconstruction workflow."""

    def __init__(self, session_dir: Path, config: dict):
        self.session_dir = session_dir
        self.input_dir = session_dir / "inputs"
        self.output_dir = session_dir / "outputs"
        self.config = config

    def run(self, progress_callback):
        """Execute full pipeline with progress updates."""

        # Step 1: Validate inputs (10%)
        progress_callback("Validating uploaded files...", 10)
        input_files = self.validate_inputs()

        # Step 2: Create brain masks (30%)
        progress_callback("Creating brain masks...", 30)
        mask_files = self.create_masks(input_files)

        # Step 3: Preprocess images (50%)
        progress_callback("Preprocessing images...", 50)
        self.preprocess(input_files, mask_files)

        # Step 4: Run NeSVoR reconstruction (90%)
        progress_callback("Reconstructing 3D volume (this may take several minutes)...", 60)
        self.reconstruct()

        # Step 5: Finalize (100%)
        progress_callback("Finalizing results...", 100)
        return self.output_dir / "recon.nii.gz"

    def create_masks(self, input_files):
        """Create brain masks using nesvor segment-stack."""
        mask_dir = self.output_dir / "masks"
        mask_dir.mkdir(parents=True, exist_ok=True)

        mask_files = []
        for f in input_files:
            mask_path = mask_dir / f"{f.stem}_mask.nii.gz"
            mask_files.append(mask_path)

        create_brain_masks(
            [str(f) for f in input_files],
            [str(m) for m in mask_files]
        )
        return mask_files

    def preprocess(self, input_files, mask_files):
        """Crop and mask images."""
        preproc_dir = self.output_dir / "preproc"
        preproc_dir.mkdir(parents=True, exist_ok=True)

        process_masks_and_images(
            list_of_files=[str(f) for f in input_files],
            list_of_masks=[str(m) for m in mask_files],
            output_folder=str(preproc_dir)
        )

    def reconstruct(self):
        """Run NeSVoR reconstruction."""
        preproc_dir = self.output_dir / "preproc"

        # Find preprocessed files and masks
        input_stacks = sorted(preproc_dir.glob("*.nii.gz"))
        input_stacks = [f for f in input_stacks if "_mask" not in f.name]
        mask_stacks = sorted(preproc_dir.glob("*_mask.nii.gz"))

        # Build nesvor command
        cmd = [
            "nesvor", "reconstruct",
            "--input-stacks", *[str(f) for f in input_stacks],
            "--stack-masks", *[str(m) for m in mask_stacks],
            "--output-volume", str(self.output_dir / "recon.nii.gz"),
            "--output-resolution", str(self.config.get("resolution", 0.8)),
            "--n-levels-bias", "1",
        ]

        if self.config.get("bias_correction", True):
            cmd.append("--bias-field-correction")

        subprocess.run(cmd, check=True)
```

### 3. Storage Manager (`webapp/storage.py`)

```python
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time

STORAGE_DIR = Path("/app/data/sessions")
RETENTION_DAYS = 7

class SessionManager:
    """Manages user sessions and file storage with 7-day retention."""

    @classmethod
    def create_session(cls) -> "Session":
        """Create a new session with unique ID."""
        session_id = str(uuid.uuid4())[:8]
        session_dir = STORAGE_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Store creation timestamp
        (session_dir / ".created").write_text(datetime.now().isoformat())

        return Session(session_id, session_dir)

    @classmethod
    def get_session(cls, session_id: str) -> "Session":
        """Retrieve existing session."""
        session_dir = STORAGE_DIR / session_id
        if session_dir.exists():
            return Session(session_id, session_dir)
        return None

    @classmethod
    def cleanup_old_sessions(cls):
        """Remove sessions older than 7 days."""
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

        for session_dir in STORAGE_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            created_file = session_dir / ".created"
            if created_file.exists():
                created = datetime.fromisoformat(created_file.read_text())
                if created < cutoff:
                    shutil.rmtree(session_dir)


class Session:
    """Represents a user session."""

    def __init__(self, session_id: str, session_dir: Path):
        self.session_id = session_id
        self.session_dir = session_dir
        self.input_dir = session_dir / "inputs"
        self.output_dir = session_dir / "outputs"

    def save_uploaded_files(self, files):
        """Save uploaded files to session directory."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for f in files:
            path = self.input_dir / f.name
            path.write_bytes(f.read())
            saved.append(path)
        return saved

    def has_results(self) -> bool:
        """Check if reconstruction results exist."""
        return (self.output_dir / "recon.nii.gz").exists()

    def get_result_path(self) -> Path:
        """Get path to reconstruction result."""
        return self.output_dir / "recon.nii.gz"

    def get_download_url(self) -> str:
        """Get shareable download URL."""
        return f"/download/{self.session_id}"

    def days_remaining(self) -> int:
        """Days until session expires."""
        created_file = self.session_dir / ".created"
        created = datetime.fromisoformat(created_file.read_text())
        expires = created + timedelta(days=RETENTION_DAYS)
        remaining = (expires - datetime.now()).days
        return max(0, remaining)


# Background cleanup thread
def start_cleanup_scheduler():
    """Run cleanup every hour."""
    def cleanup_loop():
        while True:
            SessionManager.cleanup_old_sessions()
            time.sleep(3600)  # 1 hour

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
```

### 4. Visualization (`webapp/visualization.py`)

```python
import nibabel as nib
import numpy as np
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components

def display_slices(nifti_path):
    """Display 2D orthogonal slices of the reconstruction."""
    img = nib.load(nifti_path)
    data = img.get_fdata()

    # Normalize for display
    data = (data - data.min()) / (data.max() - data.min() + 1e-8)

    # Get middle slices
    mid_x = data.shape[0] // 2
    mid_y = data.shape[1] // 2
    mid_z = data.shape[2] // 2

    # Create three columns for orthogonal views
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Axial**")
        fig = px.imshow(np.rot90(data[:, :, mid_z]), color_continuous_scale='gray')
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Coronal**")
        fig = px.imshow(np.rot90(data[:, mid_y, :]), color_continuous_scale='gray')
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown("**Sagittal**")
        fig = px.imshow(np.rot90(data[mid_x, :, :]), color_continuous_scale='gray')
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)


def create_niivue_viewer(nifti_url: str):
    """
    Embed NiiVue 3D viewer using iframe.

    NiiVue is a WebGL2-based NIfTI viewer that provides interactive
    3D volume rendering directly in the browser.
    """
    niivue_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/@niivue/niivue@latest/dist/niivue.umd.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #gl {{ width: 100%; height: 500px; }}
        </style>
    </head>
    <body>
        <canvas id="gl"></canvas>
        <script>
            const nv = new niivue.Niivue({{
                show3Dcrosshair: true,
                backColor: [0.2, 0.2, 0.3, 1]
            }});
            nv.attachToCanvas(document.getElementById('gl'));
            nv.loadVolumes([{{ url: '{nifti_url}' }}]);
        </script>
    </body>
    </html>
    """

    components.html(niivue_html, height=520)


def display_results(session):
    """Display reconstruction results with preview and download."""
    result_path = session.get_result_path()

    st.header("Step 3: Results")

    # Download button
    with open(result_path, "rb") as f:
        st.download_button(
            label="Download Reconstruction",
            data=f,
            file_name="recon.nii.gz",
            mime="application/gzip"
        )

    st.info(f"Results available for {session.days_remaining()} more days")

    # 2D slice preview
    st.subheader("Preview")
    display_slices(result_path)

    # Optional 3D viewer
    with st.expander("Open 3D Viewer (NiiVue)"):
        st.markdown("""
        Interactive 3D volume rendering. Use mouse to rotate, scroll to zoom.
        """)
        download_url = session.get_download_url()
        create_niivue_viewer(download_url)
```

---

## Docker Configuration

### Dockerfile.webapp

```dockerfile
FROM junskenxu/nesvor:latest

# Install web application dependencies
RUN pip install --no-cache-dir \
    streamlit==1.29.0 \
    nibabel>=3.2.0 \
    numpy>=1.19.0 \
    plotly>=5.0.0

WORKDIR /app

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data/sessions

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "webapp/app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true", \
            "--server.maxUploadSize=500"]
```

### docker-compose.webapp.yml

```yaml
version: '3.8'

services:
  fetal-mri-webapp:
    build:
      context: .
      dockerfile: Dockerfile.webapp
    container_name: fetal-mri-reconstruction
    ports:
      - "8501:8501"
    volumes:
      # Persistent storage for sessions (7-day retention)
      - fetal_mri_data:/app/data/sessions
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    restart: unless-stopped
    # Resource limits
    mem_limit: 32g
    shm_size: 8g

volumes:
  fetal_mri_data:
    driver: local
```

---

## Requirements

### requirements.webapp.txt

```
# Core
streamlit>=1.29.0
nibabel>=3.2.0
numpy>=1.19.0

# Visualization
plotly>=5.0.0
matplotlib>=3.5.0

# NeSVoR (provided by base image)
# nesvor
```

---

## Deployment

### Quick Start

```bash
# Build and run
docker-compose -f docker-compose.webapp.yml up -d

# View logs
docker-compose -f docker-compose.webapp.yml logs -f

# Access at http://localhost:8501
```

### Production Deployment

For production, consider:
1. **Reverse proxy** (nginx) with HTTPS
2. **Domain name** for easy access
3. **GPU monitoring** to track utilization
4. **Backup strategy** for session data

---

## Implementation Order

### Phase 1: Core Application (MVP)
1. Create `webapp/` directory structure
2. Implement `webapp/app.py` - main Streamlit interface
3. Implement `webapp/processing.py` - pipeline wrapper
4. Implement `webapp/storage.py` - session management
5. Create `Dockerfile.webapp` and `docker-compose.webapp.yml`
6. Test end-to-end locally

### Phase 2: Visualization & Polish
1. Implement `webapp/visualization.py` - 2D slice previews
2. Add NiiVue 3D viewer integration
3. Improve error handling and user messages
4. Add input validation

### Phase 3: Production Ready
1. Add progress estimation based on file count/size
2. Add download link sharing
3. Write user documentation
4. Performance testing with real data

---

## Summary

This updated plan provides:

| Feature | Implementation |
|---------|---------------|
| **Clean frontend** | Streamlit (no notebook visible) |
| **GPU processing** | Docker with nvidia runtime |
| **7-day storage** | Session-based with auto-cleanup |
| **2D previews** | Plotly orthogonal slices |
| **3D viewer** | NiiVue (WebGL2) embedded |
| **Simple UX** | Upload → Process → Download |

The application runs as a single Docker container that includes both the web interface and the NeSVoR processing engine.
