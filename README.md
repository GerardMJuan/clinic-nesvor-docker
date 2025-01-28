# Docker NesVor Clinic

A Docker-based implementation of the NesVor super-resolution reconstruction pipeline for clinical use, with ease of use and added preprocessing. This implementation provides a streamlined way to reconstruct fetal MRI using the NesVor algorithm.

## Overview

This repository contains a dockerized version of the NesVor reconstruction pipeline, which:
1. Performs brain extraction/masking
2. Processes and crops the images based on masks
3. Runs super-resolution reconstruction

## Prerequisites

- Docker
- NVIDIA GPU with CUDA support
- nvidia-docker

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd DockerNesvorClinic
```

2. Build the Docker image:
```bash
docker build -t docker-nesvor-clinic .
```

3. Model is already available in dockerhub:

[`docker pull gerardmartijuan/docker-nesvor-clinic`](https://hub.docker.com/r/gerardmartijuan/docker-nesvor-clinic)

## Usage

1. Prepare your data:
   - Create an `input` directory with your .nii.gz files
   - Create an `output` directory for results

2. Run the reconstruction:
```bash
./run_docker_nesvor.sh
```

The script will:
- Mount your input/output directories to the container
- Process all .nii.gz files in the input directory
- Generate the reconstruction in the output directory as `recon.nii.gz`

## Output Structure

```
output/
├── masks/           # Brain masks
├── preproc/        # Preprocessed images and masks
└── recon.nii.gz    # Final reconstructed volume
```

## Parameters

The reconstruction uses the following default parameters:
- Output resolution: 0.8mm isotropic
- Bias field correction enabled
- Single level bias field correction

## Notes

- Input images must be in NIfTI format (.nii.gz)
- All input images must be from the same subject
- The pipeline requires GPU acceleration

## License

This project is built upon NesVoR. Please see their license for terms of use.

https://github.com/daviddmc/NeSVoR

## Citation

If you use this pipeline in your research, please cite the original NesVoR paper:

[EbnerWang2020] Ebner, M., Wang, G., Li, W., Aertsen, M., Patel, P. A., Aughwane, R., Melbourne, A., Doel, T., Dymarkowski, S., De Coppi, P., David, A. L., Deprest, J., Ourselin, S., Vercauteren, T. (2020). An automated framework for localization, segmentation and super-resolution reconstruction of fetal brain MRI. NeuroImage, 206, 116324.