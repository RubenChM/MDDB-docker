import os
import gradio as gr

# Internal service URL for Docker Swarm communication
base_url = f"http://rest:{os.getenv('REST_INNER_PORT', 3000)}/rest/v1/"

# Get root_path from environment or default to 'mcp_rest'
root_path = os.getenv("MCP_ROOT_PATH", "mcp_rest")

# Ensure root_path doesn't have leading/trailing slashes
root_path = root_path.strip('/')

app = gr.load_openapi(
    openapi_spec="./swagger.json",
    base_url=base_url,
    paths=["^/projects$"],
    methods=["GET"],
    auth_token=os.getenv("OPENAPI_AUTH_TOKEN")
)

app.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("MCP_PORT", 8000)),
    root_path=root_path,
    mcp_server=True,
    allowed_paths=["."]
)
