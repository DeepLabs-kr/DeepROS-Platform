"""API routes and endpoints."""

from fastapi import APIRouter
from app.api.v1 import ros_domains, nodes, node_connections, node_messages

api_router = APIRouter()

# Include all API routes
api_router.include_router(ros_domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(node_connections.router, prefix="/connections", tags=["connections"])
api_router.include_router(node_messages.router, prefix="/messages", tags=["messages"]) 