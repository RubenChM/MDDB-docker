# Base docker with miniconda
FROM docker.io/continuumio/miniconda3:latest

# Define working dir
WORKDIR /app

# Install libgl1 for avoiding problems with VMD and fuse for using fusermount and goofys
RUN apt-get update && \
    apt-get install -y libgl1 && \
    apt-get install -y fuse curl

# Download goofys and make it executable
# RUN wget https://github.com/kahing/goofys/releases/latest/download/goofys
COPY goofys .
RUN chmod +x goofys 

# Define the build arguments
ARG VERSION

# If version is set, wget the specific version of the workflow
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        git clone --branch master --depth 1 https://github.com/mmb-irb/MDDB-workflow.git; \
        curl -s "https://api.github.com/repos/mmb-irb/MDDB-workflow/tags" \
            | grep -m 1 '"name":' \
            | sed -E 's/.*"name": "v?([^"]+)".*/\1/' > version.txt; \
    else \
        git clone --branch v${VERSION} --depth 1 https://github.com/mmb-irb/MDDB-workflow.git; \
        echo "$VERSION" > version.txt; \
    fi

# Enable libmamba as solver
RUN conda config --set solver libmamba

# Create new environment
RUN conda env create --file=/app/MDDB-workflow/envs/environment.yml && conda clean -afy

# Install mwf SW
WORKDIR /app/MDDB-workflow
RUN conda run -n mwf_env python -m pip install -e .

# Define working dir
WORKDIR /app

# Export python path
ENV PYTHONPATH="${PYTHONPATH}:/app/MDDB-workflow"

# Define arguments passed from docker-compose
ARG MINIO_USER
ARG MINIO_PASSWORD
ARG MINIO_API_PORT

# Set the environment variables
ENV MINIO_USER=$MINIO_USER
ENV MINIO_PASSWORD=$MINIO_PASSWORD
ENV MINIO_API_PORT=$MINIO_API_PORT

# Code to run when container is started
RUN echo '#!/bin/sh' > entrypoint.sh && \
    echo 'if [ -n "$BUCKET" ]; then' >> entrypoint.sh && \
    echo '  export AWS_ACCESS_KEY_ID=$MINIO_USER' >> entrypoint.sh && \
    echo '  export AWS_SECRET_ACCESS_KEY=$MINIO_PASSWORD' >> entrypoint.sh && \
    echo '  /app/goofys --endpoint http://minio:$MINIO_API_PORT $BUCKET /mnt' >> entrypoint.sh && \
    echo 'fi' >> entrypoint.sh && \
    echo 'conda run --no-capture-output -n mwf_env "$@"' >> entrypoint.sh && \
    echo 'if [ -n "$BUCKET" ]; then' >> entrypoint.sh && \
    echo '  fusermount -u /mnt' >> entrypoint.sh && \
    echo 'fi' >> entrypoint.sh && \
    chmod +x entrypoint.sh

# Serve the app
ENTRYPOINT ["/app/entrypoint.sh"]
