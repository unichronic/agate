from __future__ import annotations

import os
import re
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AGATE Unified Gateway", version="0.1.0")

OPA_URL = os.getenv("OPA_URL", "http://localhost:8181/v1/data/agate/allow")
PRESIDIO_URL = os.getenv("PRESIDIO_URL", "http://localhost:8081/analyze")
LAKERA_URL = os.getenv("LAKERA_URL", "")
LAKERA_API_KEY = os.getenv("LAKERA_API_KEY", "")

INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s+override",
    r"exfiltrate",
    r"send\s+all\s+.*\s+to\s+[^\s]+@",
]


class ToolCall(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)


class AgentRequest(BaseModel):
    user_id: str
    role: str
    prompt: str
    source: str = "ticket"
    tool_call: ToolCall | None = None
    response_preview: str | None = None


def local_injection_scan(text: str) -> Dict[str, Any]:
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return {"blocked": True, "reason": f"local_pattern:{pattern}"}
    return {"blocked": False, "reason": "clean"}


def optional_lakera_scan(text: str) -> Dict[str, Any]:
    if not LAKERA_URL or not LAKERA_API_KEY:
        return {"checked": False, "blocked": False, "reason": "lakera_not_configured"}
    try:
        # API shape varies by plan/version; this is intentionally adapter-friendly.
        resp = requests.post(
            LAKERA_URL,
            headers={"Authorization": f"Bearer {LAKERA_API_KEY}"},
            json={"input": text},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        flagged = bool(data.get("flagged") or data.get("malicious"))
        return {"checked": True, "blocked": flagged, "reason": data}
    except Exception as exc:  # broad because external API contract may vary
        return {"checked": True, "blocked": False, "reason": f"lakera_error:{exc}"}


def opa_allow(input_doc: Dict[str, Any]) -> Dict[str, Any]:
    try:
        resp = requests.post(OPA_URL, json={"input": input_doc}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        decision = bool(data.get("result", False))
        return {"allowed": decision, "raw": data}
    except Exception as exc:
        return {"allowed": False, "raw": {"error": str(exc)}}


def presidio_analyze(text: str) -> Dict[str, Any]:
    try:
        payload = {"text": text, "language": "en"}
        resp = requests.post(PRESIDIO_URL, json=payload, timeout=5)
        resp.raise_for_status()
        findings = resp.json()
        return {"checked": True, "findings": findings}
    except Exception as exc:
        return {"checked": False, "findings": [], "error": str(exc)}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/agent/guard")
def guard(request: AgentRequest) -> Dict[str, Any]:
    local_scan = local_injection_scan(request.prompt)
    if local_scan["blocked"]:
        raise HTTPException(status_code=403, detail={"stage": "input", **local_scan})

    lakera_scan = optional_lakera_scan(request.prompt)
    if lakera_scan["blocked"]:
        raise HTTPException(status_code=403, detail={"stage": "input", **lakera_scan})

    tool_decision = {"allowed": True, "raw": {"note": "no_tool_call"}}
    if request.tool_call:
        tool_decision = opa_allow(
            {
                "user_id": request.user_id,
                "role": request.role,
                "source": request.source,
                "tool": request.tool_call.tool,
                "args": request.tool_call.args,
            }
        )
        if not tool_decision["allowed"]:
            raise HTTPException(
                status_code=403,
                detail={"stage": "tool_policy", "reason": "opa_deny", "opa": tool_decision["raw"]},
            )

    dlp = {"checked": False, "findings": []}
    if request.response_preview:
        dlp = presidio_analyze(request.response_preview)
        if dlp["checked"] and dlp.get("findings"):
            raise HTTPException(status_code=403, detail={"stage": "output_dlp", "presidio": dlp})

    return {
        "allowed": True,
        "input_scan": local_scan,
        "lakera_scan": lakera_scan,
        "tool_policy": tool_decision,
        "output_dlp": dlp,
    }
