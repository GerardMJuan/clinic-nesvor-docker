"""Configuration settings for the Fetal MRI Reconstruction web application."""

from pathlib import Path
import os

# Storage settings
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "/app/data/sessions"))
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", 7))

# Processing defaults
DEFAULT_RESOLUTION = 0.8  # mm
DEFAULT_BIAS_CORRECTION = True
DEFAULT_BOUNDARY_PADDING = 15  # mm

# Upload limits
MAX_UPLOAD_SIZE_MB = 500
MAX_FILES = 10

# UI settings
APP_TITLE = "Fetal Brain MRI Reconstruction"
APP_DESCRIPTION = "Transform 2D MRI slices into high-resolution 3D volumes"

# Error messages
ERROR_MESSAGES = {
    "no_gpu": "GPU not available. This tool requires an NVIDIA GPU for reconstruction.",
    "empty_mask": "Could not detect brain in image '{filename}'. Please check the input file.",
    "reconstruction_failed": "Reconstruction failed. This may happen with low-quality inputs or incompatible files.",
    "timeout": "Processing took too long. Try with fewer input files.",
    "invalid_file": "Invalid NIfTI file: '{filename}'. Please ensure the file is a valid .nii.gz format.",
    "no_files": "Please upload at least one MRI stack file.",
    "too_many_files": f"Maximum {MAX_FILES} files allowed per session.",
}
