"""Backup functionality for reconstruction results."""

import shutil
import logging
from pathlib import Path
from datetime import datetime

from webapp.config import BACKUP_ENABLED, BACKUP_DIR

logger = logging.getLogger(__name__)


def backup_result(session_id: str, result_path: Path) -> bool:
    """
    Backup a reconstruction result to the backup directory.

    The backup is organized by date and session ID:
        BACKUP_DIR/
        ├── 2024-01-15/
        │   ├── abc123_recon.nii.gz
        │   └── def456_recon.nii.gz
        └── 2024-01-16/
            └── ghi789_recon.nii.gz

    Args:
        session_id: The session identifier
        result_path: Path to the reconstruction result file

    Returns:
        True if backup succeeded, False otherwise
    """
    if not BACKUP_ENABLED:
        logger.debug("Backup disabled, skipping")
        return False

    if not result_path.exists():
        logger.warning(f"Result file not found: {result_path}")
        return False

    try:
        # Create date-based backup folder
        today = datetime.now().strftime("%Y-%m-%d")
        backup_folder = BACKUP_DIR / today
        backup_folder.mkdir(parents=True, exist_ok=True)

        # Create backup filename with session ID
        backup_filename = f"{session_id}_recon.nii.gz"
        backup_path = backup_folder / backup_filename

        # Copy file
        shutil.copy2(result_path, backup_path)
        logger.info(f"Backed up result to: {backup_path}")

        return True

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False


def get_backup_stats() -> dict:
    """
    Get backup statistics.

    Returns:
        Dictionary with backup stats
    """
    if not BACKUP_ENABLED or not BACKUP_DIR.exists():
        return {
            "enabled": BACKUP_ENABLED,
            "total_backups": 0,
            "total_size_mb": 0,
            "backup_dir": str(BACKUP_DIR)
        }

    total_files = 0
    total_size = 0

    for date_folder in BACKUP_DIR.iterdir():
        if date_folder.is_dir():
            for backup_file in date_folder.glob("*.nii.gz"):
                total_files += 1
                total_size += backup_file.stat().st_size

    return {
        "enabled": BACKUP_ENABLED,
        "total_backups": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 1),
        "backup_dir": str(BACKUP_DIR)
    }
