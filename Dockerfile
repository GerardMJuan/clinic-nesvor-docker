# Stage 1: install from Nesvor
FROM junshenxu/nesvor:latest

# Set up application
WORKDIR /app
COPY . .

# Make script executable
RUN chmod +x run_recon.sh

# Define entrypoint
ENTRYPOINT ["./run_recon.sh"]