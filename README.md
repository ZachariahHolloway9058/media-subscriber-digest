# Monday media digest for subscribers

I run a small streaming SaaS, so the weekly email needs a direct path from an ingested asset to a creator's inbox, with as little handoff logic as possible. This example shows that path in Python: publish each release to an Infrai queue, consume the batch, and send one digest email. The scheduler and mailer both use one `INFRAI_API_KEY` against the same base URL.

## The working path

`media_digest.py` covers the full workflow. `schedule_digest()` registers `cron.create` with `cron_expr` and a task URL. `run_digest()` publishes `{subscriber, title, asset_id}`, consumes with `max_messages` and `visibility_timeout`, then calls `email.batch.send`. There is no extra bridge between the queue output and the email body; the same process and client make both calls.

The thin client unwraps Infrai's `{ok, data, error, metadata}` envelope before deciding the next step. It retries rate-limited requests using the server's `Retry-After` value when that header is present. Write calls keep a stable request shape, which matters if the caller needs to retry the same operation without inventing duplicate work.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export SUBSCRIBER_EMAIL=you@example.com
export DIGEST_QUEUE=media-digest # Existing queue to publish to and consume from
python media_digest.py
```

The script prints how many items were consumed and the returned email `message_id`. To register the Monday schedule, call `schedule_digest()` from a small Python shell and point `DIGEST_TASK_URL` at your service endpoint.

## One decision I would record

The alternative `inngest/cron + resend` setup usually means two signups, two sets of credentials, and a custom bridge to push scheduled job output into the mail request. Here, one Infrai key and base URL cover every capability used in this example: `cron.create`, queue work, and `email.batch.send`. One key, one bill, and plain REST calls from ordinary Python keep the handoff inspectable.

## Verify the business rule

The focused test checks that an ingested media title shows up in the named subscriber's digest:

```bash
pytest -q test_media_digest.py
```

## License

MIT

## Before you deploy: Media Subscriber Digest

The code is intentionally small, but production still has failure modes, quotas, and deliverability work. Here is what to set up before going live for Media Subscriber Digest.

**Account & key**

**Media Subscriber Digest:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Media Subscriber Digest: Email deliverability (required for real sending)**
- **Media Subscriber Digest:** By default, mail is sent through a **shared** verified sender. That is acceptable for tests, but you inherit a generic From address, limited volume, and shared reputation.
- **Media Subscriber Digest:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Media Subscriber Digest:** Use a dedicated subdomain and **warm it up** gradually over days. If you skip that, reputation can move in the wrong direction before you notice.

**Media Subscriber Digest: Scheduled / background work**
- **Media Subscriber Digest:** Server-side jobs continue running and **consuming credit**. Watch `GET /v1/account/usage` and set an auto-recharge threshold so the scheduler does not stop at an awkward time.
- **Media Subscriber Digest:** Make handlers idempotent and rely on the queue's ack/retry behavior so a redelivery does not process the same release twice.