# Use nginx Alpine Linux as base image
FROM docker.io/library/nginx:alpine

# Define the build arguments
ARG VERSION
ARG CLIENT_INNER_PORT

# This ARG will hold the label value
ARG LABEL_VERSION

# Define working dir
WORKDIR /app

# If version is set, wget the specific version of the client build
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip; \
        LABEL_VERSION=$(curl -s "https://api.github.com/repos/mmb-irb/MDposit-client-build/tags" | grep -m 1 '"name":' | sed -E 's/.*"name": "([^"]+)".*/\1/'); \
    else \
        wget https://raw.githubusercontent.com/mmb-irb/MDposit-client-build/v$VERSION/build.zip; \
        LABEL_VERSION="$VERSION"; \
    fi \ &&
    echo "$LABEL_VERSION" > /app/version.txt


ARG LABEL_VERSION
LABEL version="${LABEL_VERSION}"

# Download and unzip mdposit-client-build repo
# RUN wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip
RUN unzip build.zip

# Copy the built React app to nginx
RUN cp -r /app/build/* /usr/share/nginx/html

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]