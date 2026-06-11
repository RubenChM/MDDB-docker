import os
import gradio as gr
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RootPathMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check for X-Forwarded-Path header set by Apache
        forwarded_path = request.headers.get("X-Forwarded-Path", "")
        if forwarded_path:
            # Update ASGI scope's root_path for this request
            request.scope["root_path"] = forwarded_path
        return await call_next(request)


# Internal service URL for Docker Swarm communication
base_url = f"http://rest:{os.getenv('REST_INNER_PORT', 3000)}/rest/v1/"

app = gr.load_openapi(
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
)

# Add middleware to handle X-Forwarded-Path
app.app.add_middleware(RootPathMiddleware)

app.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("MCP_PORT", 8000)),
    root_path=f'/{os.getenv("MCP_ROOT_PATH", "mcp_rest")}',
    mcp_server=True
)
