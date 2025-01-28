#!/bin/bash

# Define directories
INPUT_DIR="/app/data/inputs"
OUTPUT_DIR="/app/data/outputs"

# Check if directories exist
if [ ! -d "$INPUT_DIR" ] || [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Input or output directory does not exist"
    exit 1
fi

# Assume preprocessing is done

# Enable nullglob to prevent issues if no files match pattern
shopt -s nullglob

# Get list of mask files directly
list_of_masks=("$OUTPUT_DIR"/preproc/*_mask.nii.gz)
list_of_files=()

# Find corresponding input files for each mask
for mask in "${list_of_masks[@]}"; do
    file="${mask%_mask.nii.gz}.nii.gz"
    if [ -f "$file" ]; then
        list_of_files+=("$file")
    else
        echo "Warning: Input file not found for mask $mask"
        exit 1
    fi
done

# Check if we found any files
if [ ${#list_of_files[@]} -eq 0 ]; then
    echo "Error: No .nii.gz files found in input directory"
    exit 1
fi

# Create recon directory in output directory
mkdir -p "$OUTPUT_DIR/recon"

# Run reconstruction pipeline
echo "Running reconstruction pipeline..."
nesvor reconstruct \
    --input-stacks "${list_of_files[@]}" \
    --stack-masks "${list_of_masks[@]}" \
    --output-volume "$OUTPUT_DIR/recon/nesvor.nii.gz" \
    --output-model "$OUTPUT_DIR/recon/nesvor.pt" \
    --output-resolution 0.8 \
    --n-levels-bias 1 \
    --bias-field-correction

# Check for output files and logs
if [ ! -f "$OUTPUT_DIR/recon/nesvor.nii.gz" ]; then
    echo "An error has happened during reconstruction"
    exit 1
fi

# If we get here, the output exists, so move it
mv "$OUTPUT_DIR/recon/nesvor.nii.gz" "$OUTPUT_DIR/recon.nii.gz"
