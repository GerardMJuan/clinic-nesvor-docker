"""Processing pipeline for fetal MRI reconstruction."""

import subprocess
import logging
from pathlib import Path
from typing import Callable
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.utils import create_brain_masks, process_masks_and_images
from webapp.config import DEFAULT_RESOLUTION, DEFAULT_BIAS_CORRECTION

logger = logging.getLogger(__name__)


class ReconstructionError(Exception):
    """Custom exception for reconstruction errors."""
    pass


class ReconstructionPipeline:
    """Orchestrates the full fetal MRI reconstruction workflow."""

    def __init__(self, session_dir: Path, config: dict | None = None):
        self.session_dir = Path(session_dir)
        self.input_dir = self.session_dir / "inputs"
        self.output_dir = self.session_dir / "outputs"
        self.config = config or {}

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "masks").mkdir(exist_ok=True)
        (self.output_dir / "preproc").mkdir(exist_ok=True)

    def run(self, progress_callback: Callable[[str, int], None] | None = None) -> Path:
        """
        Execute full reconstruction pipeline with progress updates.

        Args:
            progress_callback: Function(message, percentage) for progress updates

        Returns:
            Path to the reconstructed volume
        """
        def update_progress(message: str, percentage: int):
            logger.info(f"[{percentage}%] {message}")
            if progress_callback:
                progress_callback(message, percentage)

        try:
            # Step 1: Validate inputs (5%)
            update_progress("Validating uploaded files...", 5)
            input_files = self.validate_inputs()
            update_progress(f"Found {len(input_files)} valid input files", 10)

            # Step 2: Create brain masks (30%)
            update_progress("Creating brain masks (this may take a few minutes)...", 15)
            mask_files = self.create_masks(input_files)
            update_progress("Brain masks created successfully", 35)

            # Step 3: Preprocess images (50%)
            update_progress("Preprocessing images (cropping and masking)...", 40)
            self.preprocess(input_files, mask_files)
            update_progress("Images preprocessed successfully", 55)

            # Step 4: Run NeSVoR reconstruction (95%)
            update_progress("Reconstructing 3D volume (this may take several minutes)...", 60)
            self.reconstruct()
            update_progress("3D reconstruction complete", 95)

            # Step 5: Finalize (100%)
            update_progress("Finalizing results...", 98)
            result_path = self.output_dir / "recon.nii.gz"

            if not result_path.exists():
                raise ReconstructionError("Reconstruction output not found")

            update_progress("Done!", 100)
            return result_path

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise ReconstructionError(str(e)) from e

    def validate_inputs(self) -> list[Path]:
        """Validate input files exist and are readable."""
        input_files = list(self.input_dir.glob("*.nii.gz")) + list(self.input_dir.glob("*.nii"))

        if not input_files:
            raise ReconstructionError("No input files found")

        # Verify files can be read
        import nibabel as nib
        valid_files = []
        for f in input_files:
            try:
                img = nib.load(str(f))
                # Check it's at least 3D
                if len(img.shape) < 3:
                    logger.warning(f"Skipping {f.name}: not a 3D volume")
                    continue
                valid_files.append(f)
            except Exception as e:
                logger.warning(f"Skipping {f.name}: {e}")

        if not valid_files:
            raise ReconstructionError("No valid NIfTI files found")

        return sorted(valid_files)

    def create_masks(self, input_files: list[Path]) -> list[Path]:
        """Create brain masks using nesvor segment-stack."""
        mask_dir = self.output_dir / "masks"

        mask_files = []
        for f in input_files:
            # Remove .nii.gz extension properly
            stem = f.name.replace(".nii.gz", "").replace(".nii", "")
            mask_path = mask_dir / f"{stem}_maskbase.nii.gz"
            mask_files.append(mask_path)

        # Call the existing create_brain_masks function
        create_brain_masks(
            [str(f) for f in input_files],
            [str(m) for m in mask_files]
        )

        # Verify masks were created
        for m in mask_files:
            if not m.exists():
                raise ReconstructionError(f"Failed to create mask: {m.name}")

        return mask_files

    def preprocess(self, input_files: list[Path], mask_files: list[Path]):
        """Crop and mask images for reconstruction."""
        preproc_dir = self.output_dir / "preproc"

        # Call the existing process_masks_and_images function
        process_masks_and_images(
            list_of_files=[str(f) for f in input_files],
            list_of_masks=[str(m) for m in mask_files],
            output_folder=str(preproc_dir)
        )

        # Verify preprocessed files exist
        preproc_files = list(preproc_dir.glob("*.nii.gz"))
        if not preproc_files:
            raise ReconstructionError("Preprocessing produced no output files")

    def reconstruct(self):
        """Run NeSVoR reconstruction."""
        preproc_dir = self.output_dir / "preproc"

        # Find preprocessed files and masks
        all_files = sorted(preproc_dir.glob("*.nii.gz"))
        input_stacks = [f for f in all_files if "_mask" not in f.name]
        mask_stacks = [f for f in all_files if "_mask" in f.name]

        if not input_stacks:
            raise ReconstructionError("No preprocessed stacks found")
        if not mask_stacks:
            raise ReconstructionError("No preprocessed masks found")

        logger.info(f"Reconstructing from {len(input_stacks)} stacks")

        # Get configuration
        resolution = self.config.get("resolution", DEFAULT_RESOLUTION)
        bias_correction = self.config.get("bias_correction", DEFAULT_BIAS_CORRECTION)

        # Build nesvor command
        cmd = [
            "nesvor", "reconstruct",
            "--input-stacks", *[str(f) for f in input_stacks],
            "--stack-masks", *[str(m) for m in mask_stacks],
            "--output-volume", str(self.output_dir / "recon.nii.gz"),
            "--output-resolution", str(resolution),
            "--n-levels-bias", "1",
        ]

        if bias_correction:
            cmd.append("--bias-field-correction")

        logger.info(f"Running: {' '.join(cmd)}")

        # Run reconstruction
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"NeSVoR stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"NeSVoR stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"NeSVoR failed: {e.stderr}")
            raise ReconstructionError(f"Reconstruction failed: {e.stderr}") from e


def run_reconstruction(
    session_dir: Path,
    config: dict | None = None,
    progress_callback: Callable[[str, int], None] | None = None,
    session_id: str | None = None
) -> Path:
    """
    Convenience function to run reconstruction pipeline.

    Args:
        session_dir: Path to session directory containing inputs/
        config: Optional configuration dict with 'resolution', 'bias_correction'
        progress_callback: Optional callback for progress updates
        session_id: Optional session ID for backup naming

    Returns:
        Path to reconstructed volume
    """
    pipeline = ReconstructionPipeline(session_dir, config)
    result_path = pipeline.run(progress_callback)

    # Backup result if enabled
    if session_id and result_path.exists():
        try:
            from webapp.backup import backup_result
            backup_result(session_id, result_path)
        except Exception as e:
            logger.warning(f"Backup failed (non-critical): {e}")

    return result_path
