from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from gmail_client import GmailClient

load_dotenv()

# FastMCP provides the @mcp.tool() decorator
mcp = FastMCP("gmail-mcp")

_client: Optional[GmailClient] = None


def get_client() -> GmailClient:
    global _client
    if _client is None:
        _client = GmailClient()
    return _client


@mcp.tool()
def get_unread_emails(max_results: int = 0) -> List[Dict[str, Any]]:
    """Return unread inbox emails with sender, subject, snippet, message id and thread id."""
    default_max = int(os.getenv("MAX_UNREAD", "10"))
    n = max_results if max_results and max_results > 0 else default_max
    n = max(1, min(n, 50))  # safety clamp
    return get_client().list_unread(max_results=n)


@mcp.tool()
def create_draft_reply(original_message_id: str, reply_body: str) -> Dict[str, Any]:
    """Create a correctly threaded Gmail draft reply to an existing message."""
    if not original_message_id or not original_message_id.strip():
        raise ValueError("original_message_id is required.")
    if not reply_body or not reply_body.strip():
        raise ValueError("reply_body is required.")
    return get_client().create_draft_reply(original_message_id.strip(), reply_body)


if __name__ == "__main__":
    # MCP over stdio (Claude Desktop launches this process and talks over stdin/stdout)
    mcp.run()
