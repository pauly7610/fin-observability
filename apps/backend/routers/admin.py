"""Admin-only endpoints for system configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import require_role
from ..key_utils import get_or_generate_key

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/generated-keys")
async def get_generated_keys(
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin"])),
):
    """
    Return auto-generated API keys (when env vars are unset).
    Use these to configure webhook clients and MCP.
    """
    webhook_key = get_or_generate_key(db, "webhook_api_key", "WEBHOOK_API_KEY")
    mcp_key = get_or_generate_key(db, "mcp_api_key", "MCP_API_KEY")
    return {
        "webhook_api_key": webhook_key,
        "mcp_api_key": mcp_key,
    }
