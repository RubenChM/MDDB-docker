import os
import gradio as gr

# Internal service URL for Docker Swarm communication
base_url = f"http://rest:{os.getenv('REST_INNER_PORT', 3000)}/rest/v1/"

gr.load_openapi(
    openapi_spec="./swagger.json",
    base_url=base_url,
    # paths=[
    #     "^/projects$",
    #     "^/projects/options$",
    #     "^/projects/summary$",
    #     "^/projects/[^/]+$",
    #     "^/projects/[^/]+/topology$",
    #     "^/projects/[^/]+/files$",
    #     "^/projects/[^/]+/filenotes$",
    #     "^/projects/[^/]+/analyses$",
    #     "^/projects/[^/]+/analyses/[^/]+$",
    #     "^/projects/[^/]+/chains$",
    #     "^/projects/[^/]+/chains/[^/]+$",
    #     "^/references/.*",
    #     "^/pointers/.*",
    #     "^/nodes$",
    #     "^/knowledge/.*",
    # ],
    methods=["GET"],
    auth_token=os.getenv("OPENAPI_AUTH_TOKEN")
).launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("MCP_PORT", 8000)),
    root_path=f'/{os.getenv("MCP_ROOT_PATH", "mcp")}',
    mcp_server=True
)
