"""
Fetal Brain MRI Reconstruction Web Application

A Streamlit-based web interface for reconstructing 3D fetal brain volumes
from 2D MRI slices using NeSVoR.
"""

import streamlit as st
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from webapp.config import (
    APP_TITLE,
    APP_DESCRIPTION,
    DEFAULT_RESOLUTION,
    DEFAULT_BIAS_CORRECTION,
    MAX_FILES,
    ERROR_MESSAGES
)
from webapp.storage import SessionManager, Session
from webapp.processing import run_reconstruction, ReconstructionError
from webapp.visualization import (
    display_results,
    display_input_preview,
    display_orthogonal_slices
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=":brain:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Start cleanup scheduler
SessionManager.start_cleanup_scheduler()


def get_session() -> Session:
    """Get or create session from Streamlit session state."""
    if "session_id" not in st.session_state:
        session = SessionManager.create_session()
        st.session_state.session_id = session.session_id
    else:
        session = SessionManager.get_session(st.session_state.session_id)
        if session is None:
            session = SessionManager.create_session()
            st.session_state.session_id = session.session_id
    return session


def run_pipeline(session: Session, files: list, resolution: float, bias_correction: bool):
    """Run the reconstruction pipeline with progress display."""

    # Save uploaded files
    with st.spinner("Saving uploaded files..."):
        session.save_uploaded_files(files)

    # Create progress display
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(message: str, percentage: int):
        progress_bar.progress(percentage / 100)
        status_text.markdown(f"**{message}**")
        session.set_status("processing", f"{percentage}|{message}")

    # Run reconstruction
    config = {
        "resolution": resolution,
        "bias_correction": bias_correction
    }

    try:
        session.set_status("processing", "Starting...")
        result_path = run_reconstruction(
            session.session_dir,
            config=config,
            progress_callback=progress_callback,
            session_id=session.session_id  # For backup
        )
        session.set_status("complete", str(result_path))
        st.success("Reconstruction complete!")
        st.rerun()

    except ReconstructionError as e:
        session.set_status("error", str(e))
        st.error(f"Reconstruction failed: {e}")
        logger.error(f"Reconstruction error: {e}")

    except Exception as e:
        session.set_status("error", str(e))
        st.error(f"Unexpected error: {e}")
        logger.exception("Unexpected error during reconstruction")


def main():
    """Main application entry point."""

    # Header
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)
    st.markdown("---")

    # Get session
    session = get_session()

    # Check if we have results already
    if session.has_results():
        display_results(session)
        st.markdown("---")

        # Option to start new reconstruction
        if st.button("Start New Reconstruction"):
            # Create new session
            new_session = SessionManager.create_session()
            st.session_state.session_id = new_session.session_id
            st.rerun()
        return

    # Check if processing is in progress
    status, message = session.get_status()
    if status == "processing":
        st.info("Processing in progress...")
        if message:
            parts = message.split("|", 1)
            if len(parts) == 2:
                try:
                    pct = int(parts[0])
                    st.progress(pct / 100)
                    st.markdown(f"**{parts[1]}**")
                except ValueError:
                    st.markdown(f"**{message}**")
        st.markdown("Please wait for the current reconstruction to complete.")
        if st.button("Refresh Status"):
            st.rerun()
        return

    # Step 1: Upload
    st.header("Step 1: Upload MRI Stacks")

    st.markdown("""
    Upload your fetal brain MRI stacks in NIfTI format (.nii.gz or .nii).

    **Recommendations:**
    - Upload 3-6 stacks acquired from different angles
    - Each stack should contain the fetal brain
    - Files should be from the same subject/session
    """)

    uploaded_files = st.file_uploader(
        "Choose NIfTI files",
        type=["nii", "gz"],
        accept_multiple_files=True,
        help=f"Upload up to {MAX_FILES} NIfTI files (.nii.gz or .nii)"
    )

    # Validate uploads
    files_valid = False
    if uploaded_files:
        # Filter to only .nii.gz and .nii files
        valid_files = [f for f in uploaded_files
                       if f.name.endswith('.nii.gz') or f.name.endswith('.nii')]

        if len(valid_files) > MAX_FILES:
            st.error(ERROR_MESSAGES["too_many_files"])
        elif valid_files:
            files_valid = display_input_preview(valid_files)
            uploaded_files = valid_files

    st.markdown("---")

    # Step 2: Configuration
    st.header("Step 2: Configure (Optional)")

    with st.expander("Advanced Settings", expanded=False):
        st.markdown("Adjust reconstruction parameters if needed. Defaults work well for most cases.")

        resolution = st.slider(
            "Output resolution (mm)",
            min_value=0.5,
            max_value=1.5,
            value=DEFAULT_RESOLUTION,
            step=0.1,
            help="Lower values = higher resolution but longer processing time"
        )

        bias_correction = st.checkbox(
            "Bias field correction",
            value=DEFAULT_BIAS_CORRECTION,
            help="Correct intensity inhomogeneities (recommended)"
        )

    st.markdown("---")

    # Step 3: Process
    st.header("Step 3: Reconstruct")

    if not uploaded_files:
        st.info("Upload MRI stacks above to begin")
        process_button = st.button("Start Reconstruction", disabled=True)
    elif not files_valid:
        st.warning("Please fix file issues above before proceeding")
        process_button = st.button("Start Reconstruction", disabled=True)
    else:
        st.markdown(f"""
        Ready to reconstruct from **{len(uploaded_files)} stack(s)** with:
        - Resolution: **{resolution} mm** isotropic
        - Bias correction: **{'Enabled' if bias_correction else 'Disabled'}**

        This process typically takes **5-15 minutes** depending on input size.
        """)

        process_button = st.button("Start Reconstruction", type="primary")

    if process_button and uploaded_files and files_valid:
        run_pipeline(session, uploaded_files, resolution, bias_correction)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
    Powered by <a href="https://github.com/daviddmc/NeSVoR">NeSVoR</a> |
    Results stored for 7 days
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
