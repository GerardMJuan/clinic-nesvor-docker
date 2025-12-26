"""Session and file storage management with automatic cleanup."""

import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time
import logging

from webapp.config import STORAGE_DIR, RETENTION_DAYS

logger = logging.getLogger(__name__)


class Session:
    """Represents a user session with associated files."""

    def __init__(self, session_id: str, session_dir: Path):
        self.session_id = session_id
        self.session_dir = session_dir
        self.input_dir = session_dir / "inputs"
        self.output_dir = session_dir / "outputs"

    def save_uploaded_files(self, files) -> list[Path]:
        """Save uploaded files to session directory."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for f in files:
            path = self.input_dir / f.name
            path.write_bytes(f.read())
            saved.append(path)
            logger.info(f"Saved uploaded file: {path}")
        return saved

    def get_input_files(self) -> list[Path]:
        """Get list of input files."""
        if not self.input_dir.exists():
            return []
        return list(self.input_dir.glob("*.nii.gz")) + list(self.input_dir.glob("*.nii"))

    def has_results(self) -> bool:
        """Check if reconstruction results exist."""
        return self.get_result_path().exists()

    def get_result_path(self) -> Path:
        """Get path to reconstruction result."""
        return self.output_dir / "recon.nii.gz"

    def get_download_url(self) -> str:
        """Get shareable download URL."""
        return f"/download/{self.session_id}"

    def days_remaining(self) -> int:
        """Days until session expires."""
        created_file = self.session_dir / ".created"
        if not created_file.exists():
            return RETENTION_DAYS
        created = datetime.fromisoformat(created_file.read_text().strip())
        expires = created + timedelta(days=RETENTION_DAYS)
        remaining = (expires - datetime.now()).days
        return max(0, remaining)

    def get_status_file(self) -> Path:
        """Get path to status file."""
        return self.session_dir / ".status"

    def set_status(self, status: str, message: str = ""):
        """Set current processing status."""
        status_file = self.get_status_file()
        status_file.write_text(f"{status}|{message}")

    def get_status(self) -> tuple[str, str]:
        """Get current processing status."""
        status_file = self.get_status_file()
        if not status_file.exists():
            return "idle", ""
        content = status_file.read_text().strip()
        if "|" in content:
            status, message = content.split("|", 1)
            return status, message
        return content, ""


class SessionManager:
    """Manages user sessions and file storage with automatic cleanup."""

    _cleanup_started = False

    @classmethod
    def ensure_storage_dir(cls):
        """Ensure storage directory exists."""
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create_session(cls) -> Session:
        """Create a new session with unique ID."""
        cls.ensure_storage_dir()
        session_id = str(uuid.uuid4())[:8]
        session_dir = STORAGE_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Store creation timestamp
        (session_dir / ".created").write_text(datetime.now().isoformat())

        logger.info(f"Created new session: {session_id}")
        return Session(session_id, session_dir)

    @classmethod
    def get_session(cls, session_id: str) -> Session | None:
        """Retrieve existing session by ID."""
        cls.ensure_storage_dir()
        session_dir = STORAGE_DIR / session_id
        if session_dir.exists():
            return Session(session_id, session_dir)
        return None

    @classmethod
    def get_or_create_session(cls, session_id: str | None = None) -> Session:
        """Get existing session or create new one."""
        if session_id:
            session = cls.get_session(session_id)
            if session:
                return session
        return cls.create_session()

    @classmethod
    def cleanup_old_sessions(cls):
        """Remove sessions older than retention period."""
        cls.ensure_storage_dir()
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        removed = 0

        for session_dir in STORAGE_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            # Skip hidden files
            if session_dir.name.startswith("."):
                continue

            created_file = session_dir / ".created"
            if created_file.exists():
                try:
                    created = datetime.fromisoformat(created_file.read_text().strip())
                    if created < cutoff:
                        shutil.rmtree(session_dir)
                        removed += 1
                        logger.info(f"Removed expired session: {session_dir.name}")
                except Exception as e:
                    logger.error(f"Error checking session {session_dir.name}: {e}")

        if removed > 0:
            logger.info(f"Cleanup complete: removed {removed} expired sessions")

    @classmethod
    def start_cleanup_scheduler(cls):
        """Start background thread for periodic cleanup."""
        if cls._cleanup_started:
            return

        def cleanup_loop():
            while True:
                try:
                    cls.cleanup_old_sessions()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
                time.sleep(3600)  # Run every hour

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        cls._cleanup_started = True
        logger.info("Started session cleanup scheduler")

    @classmethod
    def get_active_sessions_count(cls) -> int:
        """Get count of active sessions."""
        cls.ensure_storage_dir()
        return sum(1 for d in STORAGE_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))
