@echo off
setlocal enabledelayedexpansion

:: Hardcoded directories
set "INPUT_DIR=input"
set "OUTPUT_DIR=output"

:: Get absolute paths
for %%i in ("%INPUT_DIR%") do set "INPUT_DIR=%%~fi"
for %%i in ("%OUTPUT_DIR%") do set "OUTPUT_DIR=%%~fi"

:: Check if input directory exists
if not exist "%INPUT_DIR%\" (
    echo Error: Input directory %INPUT_DIR% does not exist
    pause
    exit /b 1
)

:: Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%\" (
    echo Creating output directory %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

docker run ^
    --rm ^
    --ipc=host ^
    -v "%INPUT_DIR%":/app/data/inputs ^
    -v "%OUTPUT_DIR%":/app/data/outputs ^
    gerardmartijuan/docker-niftymic-clinic:latest ^
    "run_preproc.sh"

:: Run the docker container with NVIDIA GPU support
docker run ^
    --rm ^
    --gpus=all ^
    --ipc=host ^
    -v "%INPUT_DIR%":/app/data/inputs ^
    -v "%OUTPUT_DIR%":/app/data/outputs ^
    gerardmartijuan/docker-nesvor-clinic:latest

:: Check if docker run was successful
if %ERRORLEVEL% equ 0 (
    echo Processing completed successfully
    echo Results are available in: %OUTPUT_DIR%
) else (
    echo Error: Docker container exited with an error
    pause
    exit /b 1
)

:: Add pause at the end to keep window open
pause