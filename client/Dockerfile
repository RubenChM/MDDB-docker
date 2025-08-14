# Use nginx Alpine Linux as base image
FROM docker.io/library/nginx:alpine

# Define the build arguments
ARG VERSION
ARG CLIENT_INNER_PORT
ARG LABEL

# Define working dir
WORKDIR /app

# If version is set, wget the specific version of the client build
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip; \
        LABEL=$(curl -s "https://api.github.com/repos/mmb-irb/MDposit-client-build/tags" | grep -m 1 '"name":' | sed -E 's/.*"name": "([^"]+)".*/\1/'); \
    else \
        wget https://raw.githubusercontent.com/mmb-irb/MDposit-client-build/v$VERSION/build.zip; \
        LABEL="$VERSION"; \
    fi

# Set the label for the image
LABEL version="$LABEL"

# Download and unzip mdposit-client-build repo
# RUN wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip
RUN unzip build.zip

# Copy the built React app to nginx
RUN cp -r /app/build/* /usr/share/nginx/html

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]