FROM python:3.10-slim

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

# Clone and install MDDB-optimade
RUN git clone https://github.com/mmb-irb/MDDB-optimade.git && \
    cd MDDB-optimade && \
    pip install -e .[server]

# Define working dir
WORKDIR /app/MDDB-optimade

# Copy the current directory contents into the container at /app
COPY .optimade.json /root/.optimade.json

# Perform search and replace using sed
RUN sed -i "s/DB_AUTH_USER/${DB_AUTH_USER}/g" /root/.optimade.json
RUN sed -i "s/DB_AUTH_PASSWORD/${DB_AUTH_PASSWORD}/g" /root/.optimade.json
RUN sed -i "s/DB_SERVER/${DB_SERVER}/g" /root/.optimade.json
RUN sed -i "s/DB_PORT/${DB_PORT}/g" /root/.optimade.json
RUN sed -i "s/DB_NAME/${DB_NAME}/g" /root/.optimade.json
RUN sed -i "s/DB_AUTHSOURCE/${DB_AUTHSOURCE}/g" /root/.optimade.json
RUN sed -i "s/PROTOCOL/${PROTOCOL}/g" /root/.optimade.json
RUN sed -i "s/URL/${URL}/g" /root/.optimade.json

# Expose the port where the app runs on
EXPOSE ${OPTIMADE_INNER_PORT}

# Define environment variable
ENV OPTIMADE_INNER_PORT=${OPTIMADE_INNER_PORT}

# Serve the app using exec form with shell expansion
CMD ["sh", "-c", "uvicorn optimade.server.main:app --reload --host 0.0.0.0 --port $OPTIMADE_INNER_PORT"]