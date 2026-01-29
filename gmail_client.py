from __future__ import annotations

import base64
import os
import re
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8")


def _get_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value")
    return None


def _normalize_reply_subject(subject: str) -> str:
    # Avoid "Re: Re: ..."
    if not subject:
        return "Re:"
    if re.match(r"^\s*re:\s*", subject, flags=re.IGNORECASE):
        return subject
    return f"Re: {subject}"


class GmailClient:
    def __init__(self) -> None:
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

        creds: Optional[Credentials] = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(
                        f"Missing OAuth credentials file: {creds_path}. "
                        "Download it from Google Cloud Console and place it in the project root."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    def list_unread(self, max_results: int = 10) -> List[Dict[str, Any]]:
        query = "is:unread in:inbox"
        resp = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        msgs = resp.get("messages", []) or []
        results: List[Dict[str, Any]] = []

        for m in msgs:
            msg_id = m["id"]
            full = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )

            headers = full.get("payload", {}).get("headers", []) or []
            results.append(
                {
                    "id": full.get("id"),
                    "threadId": full.get("threadId"),
                    "from": _get_header(headers, "From"),
                    "subject": _get_header(headers, "Subject"),
                    "date": _get_header(headers, "Date"),
                    "snippet": full.get("snippet"),
                }
            )
        return results

    def get_message_for_reply(self, message_id: str) -> Tuple[str, Dict[str, Optional[str]]]:
        full = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="metadata",
                 metadataHeaders=["From", "To", "Cc", "Subject", "Message-ID", "References", "Reply-To"])
            .execute()
        )
        thread_id = full.get("threadId")
        headers = full.get("payload", {}).get("headers", []) or []

        meta = {
            "from": _get_header(headers, "From"),
            "to": _get_header(headers, "To"),
            "cc": _get_header(headers, "Cc"),
            "subject": _get_header(headers, "Subject"),
            "message_id": _get_header(headers, "Message-ID"),
            "references": _get_header(headers, "References"),
            "reply_to": _get_header(headers, "Reply-To"),
        }
        if not thread_id:
            raise RuntimeError("Could not find threadId for the message.")
        if not meta["message_id"]:
            raise RuntimeError("Could not find Message-ID header for the message.")
        return thread_id, meta

    def create_draft_reply(self, original_message_id: str, reply_body: str) -> Dict[str, Any]:
        thread_id, meta = self.get_message_for_reply(original_message_id)

        # Who to reply to: Reply-To if present, else From
        to_addr = meta["reply_to"] or meta["from"]
        if not to_addr:
            raise RuntimeError("Could not determine recipient (Reply-To/From missing).")

        subject = _normalize_reply_subject(meta.get("subject") or "")

        in_reply_to = meta["message_id"]
        # References: append original Message-ID if not already included
        references = (meta.get("references") or "").strip()
        if references:
            if in_reply_to not in references:
                references = f"{references} {in_reply_to}"
        else:
            references = in_reply_to

        msg = EmailMessage()
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = references
        msg.set_content(reply_body)

        raw = _b64url_encode(msg.as_bytes())

        draft = {
            "message": {
                "raw": raw,
                "threadId": thread_id,
            }
        }

        created = self.service.users().drafts().create(userId="me", body=draft).execute()
        return {
            "draftId": created.get("id"),
            "threadId": thread_id,
        }
