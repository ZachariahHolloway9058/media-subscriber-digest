from dataclasses import dataclass
import os

from infrai_client import InfraiClient


@dataclass(frozen=True)
class Subscriber:
    email: str
    display_name: str


def build_digest(items: list[dict[str, str]], subscriber: Subscriber) -> str:
    titles = "".join(f"<li>{item['title']}</li>" for item in items)
    return f"<p>Hi {subscriber.display_name},</p><p>This week's new releases:</p><ul>{titles}</ul>"


def run_digest(subscriber: Subscriber, items: list[dict[str, str]], client: InfraiClient | None = None) -> dict:
    api = client or InfraiClient()
    queue = os.environ.get("DIGEST_QUEUE", "media-digest")
    for item in items:
        api.publish(queue, {"subscriber": subscriber.email, "title": item["title"], "asset_id": item["asset_id"]})
    queued = api.consume(queue, max_messages=len(items), visibility_timeout=60)
    processed = queued.get("messages") or queued.get("items") or []
    html = build_digest([message["payload"] for message in processed], subscriber)
    sent = api.send_digest(subscriber.email, "Your weekly media digest", html)
    return {"processed": len(processed), "message_id": sent.get("message_id")}


def schedule_digest(task_url: str | None = None, client: InfraiClient | None = None) -> str:
    api = client or InfraiClient()
    task = task_url or os.environ.get("DIGEST_TASK_URL", "https://example.com/media-digest")
    # The capability handoff is cron.create -> queue -> email.batch.send.
    return str(api.create_cron("0 9 * * 1", task).get("job_id"))


if __name__ == "__main__":
    subscriber = Subscriber(os.environ["SUBSCRIBER_EMAIL"], os.environ.get("SUBSCRIBER_NAME", "Subscriber"))
    sample = [{"asset_id": "episode-42", "title": "A studio soundcheck"}]
    print(run_digest(subscriber, sample))
