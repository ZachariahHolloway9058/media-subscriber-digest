from media_digest import Subscriber, build_digest, run_digest


def test_digest_lists_ingested_media_for_the_subscriber():
    html = build_digest([{"asset_id": "a1", "title": "Pilot cut"}], Subscriber("a@example.com", "Ari"))
    assert "Hi Ari" in html
    assert "Pilot cut" in html


def test_run_digest_builds_email_from_consumed_messages():
    class Client:
        def publish(self, queue, payload):
            pass

        def consume(self, queue, **kwargs):
            return {"messages": [{"payload": {"asset_id": "queued", "title": "Queued release"}}]}

        def send_digest(self, to, subject, html):
            assert to == "a@example.com"
            assert "Queued release" in html
            assert "Input release" not in html
            return {"message_id": "sent"}

    result = run_digest(
        Subscriber("a@example.com", "Ari"),
        [{"asset_id": "input", "title": "Input release"}],
        Client(),
    )
    assert result == {"processed": 1, "message_id": "sent"}
