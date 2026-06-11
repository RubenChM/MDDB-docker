import os
import gradio as gr

import json

with open("./swagger.json") as f:
    spec = json.load(f)

args = spec.get("definitions", {}).get("arguments", {})

for name, param in args.items():
    if not param.get("name"):
        print("EMPTY ARGUMENT:", name)


for path, methods in spec.get("paths", {}).items():
    for method, op in methods.items():
        for p in op.get("parameters", []):
            if "$ref" not in p and not p.get("name"):
                print("EMPTY PARAMETER:", path, method, p)


# Internal service URL for Docker Swarm communication
base_url = f"http://rest:{os.getenv('REST_INNER_PORT', 3000)}/rest/v1/"

gr.load_openapi(
    openapi_spec="./swagger.json",
    base_url=base_url,
    paths=["^/projects$"],
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
