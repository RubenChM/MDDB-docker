# Client

The **website client** is a **React App**.

For this project, the following repo has been used:

https://github.com/mmb-irb/mdposit-client-build/

## Dockerfile

This Dockerfile is used taking as a starting point the **build** of the client. It downloads the **build.zip** file corresponding to the **desired node**, it unzips into the **build folder** and, finally, it copies the content of this folder into a **nginx** container and exposes the port 80.

```Dockerfile
# Use nginx Alpine Linux as base image
FROM docker.io/library/nginx:alpine

# Define the build arguments
ARG VERSION
ARG CLIENT_INNER_PORT

# Version argument
WORKDIR /app

# If version is set, wget the specific version of the client build
# Otherwise, use the latest version
RUN if [ -z "$VERSION" ]; then \
        wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/build.zip; \
        curl -s "https://api.github.com/repos/mmb-irb/MDposit-client-build/tags" \
            | grep -m 1 '"name":' \
            | sed -E 's/.*"name": "v?([^"]+)".*/\1/' > version.txt; \
    else \
        wget https://raw.githubusercontent.com/mmb-irb/MDposit-client-build/v$VERSION/build.zip; \
        echo "$VERSION" > version.txt; \
    fi

# Unzip mdposit-client-build repo
RUN unzip build.zip

# Copy the built React app to nginx
RUN cp -r /app/build/* /usr/share/nginx/html

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```