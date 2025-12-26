"""Visualization components for MRI data display."""

import nibabel as nib
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from pathlib import Path
import base64


def load_nifti_data(nifti_path: Path | str) -> np.ndarray:
    """Load and normalize NIfTI data for display."""
    img = nib.load(str(nifti_path))
    data = img.get_fdata()

    # Handle 4D data by taking first volume
    if len(data.shape) == 4:
        data = data[:, :, :, 0]

    # Normalize to 0-1 range
    data_min, data_max = data.min(), data.max()
    if data_max > data_min:
        data = (data - data_min) / (data_max - data_min)
    else:
        data = np.zeros_like(data)

    return data


def display_orthogonal_slices(nifti_path: Path | str, title: str = "Preview"):
    """
    Display orthogonal slices (axial, coronal, sagittal) of a NIfTI volume.

    Args:
        nifti_path: Path to the NIfTI file
        title: Title for the display section
    """
    data = load_nifti_data(nifti_path)

    # Get middle slice indices
    mid_x = data.shape[0] // 2
    mid_y = data.shape[1] // 2
    mid_z = data.shape[2] // 2

    # Create three columns for orthogonal views
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Sagittal**")
        fig = go.Figure(data=go.Heatmap(
            z=np.rot90(data[mid_x, :, :]),
            colorscale='gray',
            showscale=False
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False, showgrid=False, scaleanchor='x'),
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Coronal**")
        fig = go.Figure(data=go.Heatmap(
            z=np.rot90(data[:, mid_y, :]),
            colorscale='gray',
            showscale=False
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False, showgrid=False, scaleanchor='x'),
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown("**Axial**")
        fig = go.Figure(data=go.Heatmap(
            z=np.rot90(data[:, :, mid_z]),
            colorscale='gray',
            showscale=False
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False, showgrid=False, scaleanchor='x'),
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)


def display_slice_with_slider(nifti_path: Path | str, axis: str = "axial"):
    """
    Display slices with an interactive slider.

    Args:
        nifti_path: Path to the NIfTI file
        axis: Which axis to slice ('axial', 'coronal', 'sagittal')
    """
    data = load_nifti_data(nifti_path)

    axis_map = {"sagittal": 0, "coronal": 1, "axial": 2}
    axis_idx = axis_map.get(axis.lower(), 2)

    max_slice = data.shape[axis_idx] - 1
    slice_idx = st.slider(
        f"{axis.capitalize()} slice",
        0, max_slice,
        max_slice // 2,
        key=f"slice_slider_{axis}"
    )

    # Extract slice based on axis
    if axis_idx == 0:
        slice_data = data[slice_idx, :, :]
    elif axis_idx == 1:
        slice_data = data[:, slice_idx, :]
    else:
        slice_data = data[:, :, slice_idx]

    fig = go.Figure(data=go.Heatmap(
        z=np.rot90(slice_data),
        colorscale='gray',
        showscale=False
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False, scaleanchor='x'),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


def create_niivue_viewer(nifti_path: Path | str):
    """
    Embed NiiVue 3D viewer for interactive volume rendering.

    NiiVue is a WebGL2-based NIfTI viewer that provides interactive
    3D volume rendering directly in the browser.

    Args:
        nifti_path: Path to the NIfTI file to display
    """
    # Read the file and encode as base64 for embedding
    nifti_path = Path(nifti_path)
    if not nifti_path.exists():
        st.error("File not found for 3D viewer")
        return

    # Read file bytes and encode
    file_bytes = nifti_path.read_bytes()
    b64_data = base64.b64encode(file_bytes).decode('utf-8')

    niivue_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/@niivue/niivue@0.43.0/dist/niivue.umd.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #1a1a2e; }}
            #gl {{ width: 100%; height: 480px; }}
            .controls {{
                padding: 10px;
                background: #16213e;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            button {{
                padding: 8px 16px;
                background: #0f3460;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            button:hover {{ background: #1a5f7a; }}
        </style>
    </head>
    <body>
        <canvas id="gl"></canvas>
        <div class="controls">
            <button onclick="nv.setSliceType(nv.sliceTypeMultiplanar)">2D Views</button>
            <button onclick="nv.setSliceType(nv.sliceTypeRender)">3D Render</button>
            <button onclick="nv.setSliceType(nv.sliceType3D)">3D + Slices</button>
            <button onclick="nv.moveCrosshairInVox(0,0,1)">Slice +</button>
            <button onclick="nv.moveCrosshairInVox(0,0,-1)">Slice -</button>
        </div>
        <script>
            // Decode base64 data
            const b64Data = '{b64_data}';
            const binaryString = atob(b64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {{
                bytes[i] = binaryString.charCodeAt(i);
            }}

            // Initialize NiiVue
            const nv = new niivue.Niivue({{
                show3Dcrosshair: true,
                backColor: [0.1, 0.1, 0.2, 1],
                crosshairColor: [0, 1, 0, 0.5]
            }});
            nv.attachToCanvas(document.getElementById('gl'));

            // Load volume from bytes
            nv.loadFromArrayBuffer(bytes.buffer, 'reconstruction.nii.gz');
        </script>
    </body>
    </html>
    """

    components.html(niivue_html, height=550)


def display_results(session, show_3d: bool = True):
    """
    Display reconstruction results with preview and download options.

    Args:
        session: Session object containing results
        show_3d: Whether to show 3D viewer option
    """
    result_path = session.get_result_path()

    if not result_path.exists():
        st.warning("Results not yet available")
        return

    st.header("Results")

    # File info
    file_size_mb = result_path.stat().st_size / (1024 * 1024)
    st.markdown(f"**Reconstructed volume:** `recon.nii.gz` ({file_size_mb:.1f} MB)")

    # Download button
    with open(result_path, "rb") as f:
        st.download_button(
            label="Download Reconstruction",
            data=f,
            file_name="recon.nii.gz",
            mime="application/gzip",
            type="primary"
        )

    # Expiration notice
    days = session.days_remaining()
    if days > 0:
        st.info(f"Results available for {days} more day{'s' if days != 1 else ''}")
    else:
        st.warning("Results expire today")

    # 2D slice preview
    st.subheader("Preview")
    display_orthogonal_slices(result_path)

    # Interactive slice browser
    with st.expander("Browse slices"):
        axis = st.radio("View axis", ["Axial", "Coronal", "Sagittal"], horizontal=True)
        display_slice_with_slider(result_path, axis.lower())

    # 3D viewer (optional)
    if show_3d:
        with st.expander("3D Viewer (NiiVue)"):
            st.markdown("""
            Interactive 3D volume rendering powered by [NiiVue](https://github.com/niivue/niivue).
            - **Rotate**: Click and drag
            - **Zoom**: Scroll wheel
            - **Pan**: Right-click and drag
            """)
            create_niivue_viewer(result_path)


def display_input_preview(files: list) -> bool:
    """
    Display preview of uploaded input files.

    Args:
        files: List of uploaded file objects

    Returns:
        True if all files are valid
    """
    if not files:
        return False

    st.markdown(f"**Uploaded {len(files)} file(s):**")

    valid = True
    for f in files:
        # Check file extension
        if not (f.name.endswith('.nii.gz') or f.name.endswith('.nii')):
            st.error(f"Invalid file: {f.name} (must be .nii.gz or .nii)")
            valid = False
        else:
            st.markdown(f"- {f.name} ({f.size / (1024*1024):.1f} MB)")

    return valid
