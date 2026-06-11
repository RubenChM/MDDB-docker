import os
import gradio as gr
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import re


class RootPathMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check for X-Forwarded-Path header set by Apache
        forwarded_path = request.headers.get("X-Forwarded-Path", "")
        if forwarded_path:
            # Update ASGI scope's root_path for this request
            request.scope["root_path"] = forwarded_path
        return await call_next(request)


class AssetPathRewriteMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Get the root path from headers
        root_path = request.headers.get("X-Forwarded-Path", "")
        
        # Only rewrite HTML responses
        if root_path and "text/html" in response.headers.get("content-type", ""):
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Decode and rewrite paths
            html = body.decode("utf-8")
            # Replace /static/ and /gradio_api/ and other server paths with root_path prefix
            html = re.sub(
                r'(["\'])/(?:static|gradio_api|file|config)',
                r'\1' + root_path + r'/\g<2>',
                html
            )
            
            # Return modified response
            response = Response(
                content=html,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        
        return response


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

# Add middleware to handle X-Forwarded-Path and rewrite asset URLs
app.app.add_middleware(AssetPathRewriteMiddleware)
app.app.add_middleware(RootPathMiddleware)

app.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("MCP_PORT", 8000)),
    root_path=f'/{os.getenv("MCP_ROOT_PATH", "mcp_rest")}',
    mcp_server=True
)
