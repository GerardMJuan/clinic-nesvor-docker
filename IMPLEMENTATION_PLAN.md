# Fetal MRI Web Application - Implementation Plan

## Overview

Transform the NeSVoR Docker-based fetal MRI reconstruction tool into a user-friendly web application for clinicians.

### Goals
- **Simple interface**: Non-technical users can upload data and download results
- **Minimal configuration**: Smart defaults with optional advanced settings
- **Dual deployment**: Server-based and Google Colab options
- **Progress tracking**: Real-time feedback during processing

---

## Architecture Options

### Option A: Streamlit Web App (Recommended)

**Why Streamlit?**
- Python-native (integrates with existing code)
- Minimal frontend knowledge required
- Built-in file upload/download components
- Easy deployment (Docker, cloud, Colab)
- Professional appearance with minimal CSS

### Option B: Gradio Web App (Alternative)

**Why Gradio?**
- Even simpler API than Streamlit
- Excellent for ML/medical imaging applications
- Native Colab integration with `share=True`
- Built-in queue system for GPU processing

### Recommendation: **Streamlit** for full server deployment, **Gradio** for Colab simplicity

---

## Implementation Plan

### Phase 1: Core Web Application (Streamlit)

#### 1.1 Create Application Structure

```
clinic-nesvor-docker/
├── webapp/
│   ├── __init__.py
│   ├── app.py                 # Main Streamlit application
│   ├── processing.py          # Backend processing logic
│   ├── config.py              # Configuration management
│   └── components/
│       ├── __init__.py
│       ├── upload.py          # File upload component
│       ├── progress.py        # Progress tracking component
│       └── results.py         # Results display/download
├── docker-compose.webapp.yml  # Docker Compose for web app
├── Dockerfile.webapp          # Web app Docker image
└── colab/
    └── fetal_mri_reconstruction.ipynb  # Google Colab notebook
```

#### 1.2 Main Application (`webapp/app.py`)

**Features:**
1. **Header/Branding**: Clear title explaining the tool
2. **File Upload Section**: Drag-and-drop for .nii.gz files
3. **Configuration Panel** (collapsible):
   - Output resolution (default: 0.8mm)
   - Bias field correction toggle
4. **Progress Display**: Real-time status updates
5. **Results Section**: Preview + download button

**UI Flow:**
```
┌─────────────────────────────────────────────────────────┐
│  🧠 Fetal Brain MRI Reconstruction                      │
│  Transform 2D MRI slices into high-resolution 3D       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📁 Upload MRI Stacks                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Drag and drop .nii.gz files here              │   │
│  │  or click to browse                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Uploaded files: scan_001.nii.gz, scan_002.nii.gz      │
│                                                         │
│  ▼ Advanced Settings (optional)                        │
│    Output resolution: [0.8] mm                         │
│    ☑ Bias field correction                             │
│                                                         │
│  [🚀 Start Reconstruction]                              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Processing Status:                                     │
│  ████████████░░░░░░░░ 60%                              │
│  ✓ Uploaded 3 files                                    │
│  ✓ Brain masks created                                 │
│  ⏳ Reconstructing 3D volume...                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Results:                                               │
│  [📥 Download Reconstruction (recon.nii.gz)]           │
│                                                         │
│  Preview: [3D viewer or slice thumbnails]              │
└─────────────────────────────────────────────────────────┘
```

#### 1.3 Backend Processing (`webapp/processing.py`)

**Key Functions:**

```python
class ReconstructionPipeline:
    """Manages the reconstruction workflow."""

    def __init__(self, input_files, output_dir, config):
        self.input_files = input_files
        self.output_dir = output_dir
        self.config = config
        self.status_callback = None

    def run(self, progress_callback):
        """Execute full pipeline with progress updates."""
        # Step 1: Validate inputs
        progress_callback("Validating uploaded files...", 10)

        # Step 2: Create brain masks
        progress_callback("Creating brain masks...", 30)
        self.create_masks()

        # Step 3: Preprocess images
        progress_callback("Preprocessing images...", 50)
        self.preprocess()

        # Step 4: Run reconstruction
        progress_callback("Reconstructing 3D volume (this may take several minutes)...", 70)
        self.reconstruct()

        # Step 5: Finalize
        progress_callback("Finalizing results...", 95)
        return self.get_output_path()

    def create_masks(self):
        """Call nesvor segment-stack."""
        pass

    def preprocess(self):
        """Run prepare_recon.py logic."""
        pass

    def reconstruct(self):
        """Call nesvor reconstruct."""
        pass
```

---

### Phase 2: Docker Integration

#### 2.1 Web App Dockerfile (`Dockerfile.webapp`)

```dockerfile
FROM junskenxu/nesvor:latest

# Install web application dependencies
RUN pip install streamlit nibabel numpy plotly

WORKDIR /app
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "webapp/app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
```

#### 2.2 Docker Compose (`docker-compose.webapp.yml`)

```yaml
version: '3.8'

services:
  fetal-mri-webapp:
    build:
      context: .
      dockerfile: Dockerfile.webapp
    ports:
      - "8501:8501"
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/results:/app/results
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    restart: unless-stopped
```

---

### Phase 3: Google Colab Integration

#### 3.1 Colab Notebook (`colab/fetal_mri_reconstruction.ipynb`)

**Structure:**

```markdown
# Fetal Brain MRI Reconstruction

This notebook allows you to reconstruct 3D fetal brain volumes
from 2D MRI slices using NeSVoR.

## Step 1: Setup Environment
[Code cell: Install dependencies, mount Google Drive]

## Step 2: Upload Your MRI Files
[Code cell: File upload widget OR Google Drive path]

## Step 3: Configure Reconstruction (Optional)
[Interactive widgets for settings]

## Step 4: Run Reconstruction
[Code cell: Execute pipeline with progress bar]

## Step 5: Download Results
[Code cell: Download link or copy to Drive]
```

**Key Colab Code:**

```python
# Cell 1: Setup
!pip install -q nesvor nibabel gradio

# Mount Google Drive for easy file access
from google.colab import drive
drive.mount('/content/drive')

# Cell 2: Create Gradio Interface
import gradio as gr

def process_mri(files, resolution=0.8):
    """Process uploaded MRI files."""
    # Save uploaded files
    # Run preprocessing
    # Run reconstruction
    # Return output file
    return output_path

interface = gr.Interface(
    fn=process_mri,
    inputs=[
        gr.File(label="Upload MRI Stacks (.nii.gz)", file_count="multiple"),
        gr.Slider(0.5, 1.5, value=0.8, label="Output Resolution (mm)")
    ],
    outputs=gr.File(label="Download Reconstruction"),
    title="Fetal Brain MRI Reconstruction",
    description="Upload 2D MRI slices to generate a 3D reconstruction"
)

interface.launch(share=True)  # Creates public URL
```

---

### Phase 4: User Experience Enhancements

#### 4.1 Input Validation

```python
def validate_nifti_files(files):
    """Validate uploaded NIfTI files."""
    errors = []
    for f in files:
        # Check file extension
        if not f.name.endswith('.nii.gz'):
            errors.append(f"{f.name}: Must be .nii.gz format")
            continue

        # Check file can be loaded
        try:
            img = nib.load(f)
            # Check dimensions
            if len(img.shape) < 3:
                errors.append(f"{f.name}: Must be 3D or 4D")
        except Exception as e:
            errors.append(f"{f.name}: Invalid NIfTI file")

    return errors
```

#### 4.2 Progress Tracking

- Use Streamlit's `st.progress()` and `st.status()` components
- Log key milestones: upload, mask creation, preprocessing, reconstruction
- Provide estimated time remaining based on file count

#### 4.3 Results Visualization (Optional)

```python
def display_result_preview(nifti_path):
    """Show middle slices of the reconstruction."""
    img = nib.load(nifti_path)
    data = img.get_fdata()

    # Get middle slices
    mid_x = data.shape[0] // 2
    mid_y = data.shape[1] // 2
    mid_z = data.shape[2] // 2

    # Display using Plotly or matplotlib
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(data[mid_x, :, :].T, cmap='gray')
    axes[1].imshow(data[:, mid_y, :].T, cmap='gray')
    axes[2].imshow(data[:, :, mid_z].T, cmap='gray')

    return fig
```

#### 4.4 Email Notifications (Optional)

For long-running jobs, offer email notification when complete:
- Store email with job
- Send download link when done
- Use SendGrid or similar service

---

### Phase 5: Deployment Options

#### 5.1 Self-Hosted Server

**Requirements:**
- Linux server with NVIDIA GPU
- Docker + nvidia-container-toolkit
- 16GB+ RAM recommended
- SSD storage for temp files

**Deployment:**
```bash
docker-compose -f docker-compose.webapp.yml up -d
```

#### 5.2 Cloud Deployment

**Options:**
1. **Google Cloud Run** (with GPU): Serverless, scales to zero
2. **AWS EC2 with GPU**: g4dn.xlarge ($0.526/hr on-demand)
3. **Azure Container Instances**: GPU-enabled containers

#### 5.3 Google Colab

**Advantages:**
- Free GPU access
- No server management
- Shareable notebook
- Easy for one-off reconstructions

**Limitations:**
- 12-hour session limit
- No persistent storage (use Drive)
- Requires user interaction

---

## File-by-File Implementation

### Files to Create:

| File | Purpose | Priority |
|------|---------|----------|
| `webapp/app.py` | Main Streamlit application | High |
| `webapp/processing.py` | Backend processing logic | High |
| `webapp/config.py` | Configuration management | Medium |
| `webapp/components/upload.py` | File upload component | High |
| `webapp/components/progress.py` | Progress tracking | High |
| `webapp/components/results.py` | Results display | High |
| `Dockerfile.webapp` | Web app Docker image | High |
| `docker-compose.webapp.yml` | Docker Compose config | High |
| `colab/fetal_mri_reconstruction.ipynb` | Colab notebook | High |
| `requirements.webapp.txt` | Web app dependencies | High |

### Files to Modify:

| File | Changes | Priority |
|------|---------|----------|
| `prepare_recon.py` | Add progress callbacks | Medium |
| `run_recon.sh` | Add logging for progress | Medium |
| `README.md` | Add web app documentation | Low |

---

## Technical Decisions

### 1. Direct Python vs Docker Subprocess

**Decision**: Use direct Python calls when possible, Docker subprocess for nesvor commands.

**Rationale**:
- `nesvor segment-stack` and `nesvor reconstruct` must run in the NeSVoR environment
- Preprocessing logic (cropping, masking) can run directly in Python
- For Colab, we can install nesvor directly via pip

### 2. File Storage Strategy

**Temporary Files**:
- Store in `/tmp/fetal_mri_{session_id}/`
- Auto-cleanup after download or 24 hours

**Session Management**:
- Use UUID for each session
- Store session state in memory (Streamlit) or Redis (production)

### 3. Error Handling

**User-Friendly Errors**:
```python
ERROR_MESSAGES = {
    "no_gpu": "GPU not available. This tool requires NVIDIA GPU for reconstruction.",
    "empty_mask": "Could not detect brain in image {filename}. Please check the input.",
    "reconstruction_failed": "Reconstruction failed. This may happen with low-quality inputs.",
    "timeout": "Processing took too long. Try with fewer input files."
}
```

---

## Implementation Order

### Step 1: Basic Web Interface
1. Create `webapp/app.py` with file upload
2. Create `webapp/processing.py` with pipeline wrapper
3. Test with existing Docker container

### Step 2: Progress Tracking
1. Add progress callbacks to processing
2. Integrate with Streamlit progress bar
3. Add logging for debugging

### Step 3: Docker Integration
1. Create `Dockerfile.webapp`
2. Create `docker-compose.webapp.yml`
3. Test end-to-end deployment

### Step 4: Google Colab
1. Create Colab notebook
2. Use Gradio for simple interface
3. Test with free GPU runtime

### Step 5: Polish
1. Add input validation
2. Add result preview
3. Improve error messages
4. Write documentation

---

## Summary

This plan transforms the CLI/Docker-based NeSVoR tool into an accessible web application with:

1. **Streamlit web app** for server deployment
2. **Gradio interface** in Google Colab for free GPU access
3. **Minimal user interaction**: Upload → Click → Download
4. **Smart defaults** with optional advanced settings
5. **Real-time progress** feedback during processing

The implementation prioritizes simplicity for clinicians while maintaining the full power of the NeSVoR reconstruction pipeline.
