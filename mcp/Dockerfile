FROM python:3.11-slim

ARG MCP_INNER_PORT
ARG MCP_ROOT_PATH
ARG REST_INNER_PORT
ARG MCP_DB_NAME
ARG CLIENT_URL
ARG MCP_ACCESSION

WORKDIR /app

COPY swagger.json .

RUN sed -i "s/\$DATABASE/${MCP_DB_NAME}/g" swagger.json && \
    sed -i "s/\$CLIENT_URL/${CLIENT_URL}/g" swagger.json && \
    sed -i "s/\$ACCESSION/${MCP_ACCESSION}/g" swagger.json

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV MCP_PORT=${MCP_INNER_PORT}
ENV MCP_ROOT_PATH=${MCP_ROOT_PATH}
ENV REST_INNER_PORT=${REST_INNER_PORT}

EXPOSE ${MCP_INNER_PORT}

CMD ["python", "app.py"]