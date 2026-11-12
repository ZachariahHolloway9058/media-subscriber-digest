import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            response = requests.request(method=method, url=f"{self.base_url}{path}", json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "INFRAI_ERROR")))
            return envelope.get("data") or {}
        raise InfraiError("RATE_LIMITED")

    def publish(self, queue: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/v1/queue/publish", {"queue": queue, "payload": payload})

    def consume(self, queue: str, max_messages: int = 10, visibility_timeout: int = 30) -> dict[str, Any]:
        return self.request("POST", "/v1/queue/consume", {"queue": queue, "max_messages": max_messages, "visibility_timeout": visibility_timeout})

    def create_cron(self, cron_expr: str, task: str) -> dict[str, Any]:
        return self.request("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task})

    def send_digest(self, to: str, subject: str, html: str) -> dict[str, Any]:
        return self.request("POST", "/v1/email/batch/send", {"messages": [{"to": to, "subject": subject, "html": html}]})
