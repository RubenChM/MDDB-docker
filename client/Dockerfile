# Stage 1: Determine version and download
FROM alpine:latest AS downloader

# Define build arguments
ARG VERSION

WORKDIR /tmp

RUN apk add --no-cache wget curl

RUN if [ -z "$VERSION" ]; then \
        wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip; \
        curl -s "https://api.github.com/repos/mmb-irb/MDposit-client-build/tags" | grep -m 1 '"name":' | sed -E 's/.*"name": "([^"]+)".*/\1/' > version.txt; \
    else \
        wget https://raw.githubusercontent.com/mmb-irb/MDposit-client-build/v$VERSION/build.zip; \
        echo "$VERSION" > version.txt; \
    fi

RUN unzip build.zip

# Stage 2: Final image
FROM docker.io/library/nginx:alpine

ARG CLIENT_INNER_PORT

# Copy from downloader stage
COPY --from=downloader /tmp/build /usr/share/nginx/html
COPY --from=downloader /tmp/version.txt /tmp/version.txt

# Set label with version if provided
LABEL version="${VERSION:-unknown}"

# Add version info to a file for runtime inspection
RUN if [ -f /tmp/version.txt ]; then \
        cp /tmp/version.txt /usr/share/nginx/html/version.txt; \
    fi

# Expose port
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]