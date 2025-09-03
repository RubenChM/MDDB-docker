FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define build arguments
ARG OPTIMADE_INNER_PORT
ARG DB_AUTH_USER
ARG DB_AUTH_PASSWORD
ARG DB_SERVER
ARG DB_PORT
ARG DB_NAME
ARG DB_AUTHSOURCE
ARG PROTOCOL
ARG URL

# Define working dir
WORKDIR /app

# Clone and install optimade-python-tools
RUN git clone https://github.com/JPBergsma/optimade-python-tools.git && \
    cd optimade-python-tools && \
    git checkout JPBergsma_BioExcel && \
    pip install -e .[server]

# Define working dir
WORKDIR /app/optimade-python-tools

# Copy the current directory contents into the container at /app
COPY .optimade.json /app/optimade-python-tools/.optimade.json

# Perform search and replace using sed
RUN sed -i "s/DB_AUTH_USER/${DB_AUTH_USER}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/DB_AUTH_PASSWORD/${DB_AUTH_PASSWORD}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/DB_SERVER/${DB_SERVER}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/DB_PORT/${DB_PORT}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/DB_NAME/${DB_NAME}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/DB_AUTHSOURCE/${DB_AUTHSOURCE}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/PROTOCOL/${PROTOCOL}/g" /app/optimade-python-tools/.optimade.json
RUN sed -i "s/URL/${URL}/g" /app/optimade-python-tools/.optimade.json

# Expose the port where the app runs on
EXPOSE ${OPTIMADE_INNER_PORT}

# Define environment variable
ENV OPTIMADE_INNER_PORT=${OPTIMADE_INNER_PORT}

# Serve the app using exec form with shell expansion
CMD ["sh", "-c", "uvicorn optimade.server.main:app --reload --host 0.0.0.0 --port $OPTIMADE_INNER_PORT"]