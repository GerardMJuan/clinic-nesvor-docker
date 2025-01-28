import argparse
import os
from utils.utils import (
    create_brain_masks,
    process_masks_and_images,
)


def main(args):
    """This does all the preprocessing steps for the reconstruction pipeline."""
    # Define directories
    list_of_files = args.subjects

    output_dir = args.output_dir

    # create masks directory
    masks_dir = os.path.join(output_dir, "masks")
    os.makedirs(masks_dir, exist_ok=True)

    # create "preproc" directory
    preproc_dir = os.path.join(output_dir, "preproc")
    os.makedirs(preproc_dir, exist_ok=True)

    # Generate file paths
    list_of_masks_base = [
        f.replace(".nii.gz", "_maskbase.nii.gz") for f in list_of_files
    ]

    list_of_masks_base = [
        os.path.join(masks_dir, os.path.basename(f))
        for f in list_of_masks_base
    ]

    list_of_masks = [
        f.replace("_maskbase.nii.gz", "_mask.nii.gz")
        for f in list_of_masks_base
    ]

    list_of_masks = [
        os.path.join(preproc_dir, os.path.basename(f)) for f in list_of_masks
    ]

    list_of_crops = [
        os.path.join(preproc_dir, os.path.basename(f)) for f in list_of_files
    ]

    # Handle masks
    mask_list_exists = [os.path.exists(x) for x in list_of_masks_base]
    if not all(mask_list_exists):
        print("Creating masks...")
        create_brain_masks(list_of_files, list_of_masks_base)

    # Denoise images if needed
    # denoise_list_exists = [os.path.exists(x) for x in list_of_denoise]
    # if not all(denoise_list_exists):
    #     print("Denoising using ANTs...")
    #     for image_path, image_out_path in zip(list_of_files, list_of_denoise):
    #         denoise_image(image_path, image_out_path)

    print("Processing masks and images...")
    # Process masks and images
    process_masks_and_images(
        list_of_masks_base, list_of_masks, list_of_files, list_of_crops
    )


def parser_obj():
    """Create and configure command line argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser

    Note:
        Defines all command line arguments for the reconstruction pipeline
    """
    parser = argparse.ArgumentParser(
        description="Run reconstruction algorithm on specific subjects or on all subjects"
    )

    # --subjects: list of scans
    parser.add_argument(
        "--subjects",
        nargs="+",
        type=str,
        help="List of subjects to run the reconstruction pipeline on",
    )

    # --output_dir: output directory
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Output directory for the reconstruction pipeline",
    )

    return parser


if __name__ == "__main__":
    parser = parser_obj()
    args = parser.parse_args()
    main(args)
