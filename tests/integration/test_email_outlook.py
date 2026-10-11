from datetime import datetime, timedelta, timezone

import pytest

from integrations.email.base import EmailAuthError, EmailRateLimitError
from integrations.email.outlook import OutlookProvider
from lib.rate_limiter import RateLimiter
from tests.integration.fake_graph import FakeGraph, FakeResponse


def _no_op_rate_limiter():
    return RateLimiter(clock=lambda: 0.0, sleep=lambda _: None)


def _provider(graph, **kwargs):
    return OutlookProvider(access_token=graph.token, sender_email=graph.mailbox, session=graph,
                           rate_limiter=_no_op_rate_limiter(), sleep=lambda _: None, **kwargs)


def test_send_email_creates_then_sends_message():
    graph = FakeGraph()
    provider = _provider(graph)

    result = provider.send_email(to="lead@acme.com", subject="Quick idea", body="Hi there")

    assert result["message_id"] == "msg-1" and result["thread_id"] and result["rfc_message_id"].startswith("<msg-1@")
    create, send = graph.calls[:2]
    assert (create["method"], create["url"].endswith("/me/messages")) == ("POST", True)
    assert create["headers"]["Authorization"] == "Bearer tok"
    assert create["json"]["toRecipients"] == [{"emailAddress": {"address": "lead@acme.com"}}]
    assert create["json"]["body"] == {"contentType": "Text", "content": "Hi there"}
    assert (send["method"], send["url"].endswith("/me/messages/msg-1/send")) == ("POST", True)
    assert [m["id"] for m in graph.sent()] == ["msg-1"], "the id survives the move to Sent Items"
    assert provider.rfc_message_id("msg-1") == result["rfc_message_id"]


def test_follow_up_is_a_reply_to_the_parent_with_our_recipient_subject_and_body():
    graph = FakeGraph()
    provider = _provider(graph)
    first = provider.send_email(to="lead@acme.com", subject="old quotes", body="first")

    second = provider.send_email(to="lead@acme.com", subject="Re: old quotes", body="second",
                                 thread_id=first["thread_id"], in_reply_to_message_id=first["rfc_message_id"],
                                 parent_provider_message_id=first["message_id"])

    sent = {m["id"]: m for m in graph.sent()}
    reply = sent[second["message_id"]]
    assert second["thread_id"] == first["thread_id"] == reply["conversationId"]
    assert reply["toRecipients"] == [{"emailAddress": {"address": "lead@acme.com"}}]
    assert reply["subject"] == "Re: old quotes" and reply["body"]["content"] == "second"
    headers = {h["name"]: h["value"] for h in reply["internetMessageHeaders"]}
    assert headers["In-Reply-To"] == first["rfc_message_id"] and first["rfc_message_id"] in headers["References"]
    methods = [(c["method"], c["url"].rsplit("/v1.0", 1)[-1]) for c in graph.calls[2:]]
    rid = second["message_id"]
    assert methods == [("POST", "/me/messages/msg-1/createReply"), ("PATCH", f"/me/messages/{rid}"),
                       ("POST", f"/me/messages/{rid}/send")]


def test_follow_up_finds_parent_by_message_id_or_conversation_when_no_id_given():
    graph = FakeGraph()
    provider = _provider(graph)
    first = provider.send_email(to="lead@acme.com", subject="old quotes", body="first")

    by_rfc = provider.send_email(to="lead@acme.com", subject="Re: old quotes", body="2",
                                 in_reply_to_message_id=first["rfc_message_id"])
    by_conv = provider.send_email(to="lead@acme.com", subject="Re: old quotes", body="3", thread_id=first["thread_id"])

    assert by_rfc["thread_id"] == by_conv["thread_id"] == first["thread_id"]
    assert any("sentitems" in c["url"] for c in graph.calls)


def test_follow_up_falls_back_to_plain_send_when_parent_was_deleted():
    graph = FakeGraph()
    provider = _provider(graph)
    first = provider.send_email(to="lead@acme.com", subject="old quotes", body="first")
    del graph.messages[first["message_id"]]

    second = provider.send_email(to="lead@acme.com", subject="Re: old quotes", body="second",
                                 parent_provider_message_id=first["message_id"])

    assert second["message_id"] in {m["id"] for m in graph.sent()}
    assert second["thread_id"] != first["thread_id"]      # delivered, just not threaded


def test_retries_on_429_then_succeeds_and_gives_up_after_max_retries():
    graph = FakeGraph()
    sleeps = []
    provider = OutlookProvider(access_token="tok", session=graph, rate_limiter=_no_op_rate_limiter(), sleep=sleeps.append)
    graph.fail_next = [FakeResponse(429, headers={"Retry-After": "1"})]

    assert provider.send_email(to="lead@acme.com", subject="Hi", body="Body")["message_id"] == "msg-1"
    assert sleeps == [1.0]

    graph.fail_next = [FakeResponse(429, headers={}) for _ in range(4)]
    with pytest.raises(EmailRateLimitError):
        provider.send_email(to="lead@acme.com", subject="Hi", body="Body")


def test_bad_token_raises_auth_error_not_a_generic_failure():
    graph = FakeGraph()
    provider = _provider(graph)
    provider.access_token = "wrong"
    with pytest.raises(EmailAuthError):
        provider.send_email(to="lead@acme.com", subject="Hi", body="Body")
    with pytest.raises(EmailAuthError):
        provider.profile_email()


def test_profile_email_is_the_token_owner():
    graph = FakeGraph(mailbox="Someone@VelarqoMail.com")
    assert _provider(graph).profile_email() == "someone@velarqomail.com"


def test_list_inbox_pages_received_messages_only_from_the_window():
    graph = FakeGraph()
    provider = _provider(graph)
    provider.send_email(to="lead@acme.com", subject="old quotes", body="first")      # in Sent Items: not listed
    old = graph.receive("ancient@acme.com", "Re: old", "x", received=datetime.now(timezone.utc) - timedelta(days=40))
    fresh = [graph.receive(f"p{i}@acme.com", "Re: old quotes", "yes") for i in range(3)]

    ids = provider.list_inbox("in:anywhere newer_than:30d", max_results=10)

    assert ids == fresh and old not in ids
    listing = [c for c in graph.calls if c["url"].endswith("/me/messages") and c["method"] == "GET"][0]
    assert "isDraft eq false" in listing["params"]["$filter"] and "receivedDateTime ge" in listing["params"]["$filter"]

    # Pages through @odata.nextLink.
    graph.calls.clear()
    assert provider.list_inbox("newer_than:30d", max_results=2) == fresh[:2]
    graph.calls.clear()
    with_pages = _provider(graph)
    import integrations.email.outlook as outlook_mod
    original = outlook_mod.PAGE_SIZE
    outlook_mod.PAGE_SIZE = 2
    try:
        assert with_pages.list_inbox("newer_than:30d", max_results=10) == fresh
    finally:
        outlook_mod.PAGE_SIZE = original
    assert len([c for c in graph.calls if c["method"] == "GET"]) == 2


def test_get_message_matches_the_gmail_shape_and_flags_auto_replies():
    graph = FakeGraph()
    provider = _provider(graph)
    received = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
    mid = graph.receive("Dave@Acme.co.uk", "Re: old quotes", "<p>Yes <b>call me</b></p><blockquote>old</blockquote>",
                        conversation_id="conv-9", content_type="html", received=received)
    auto = graph.receive("info@acme.co.uk", "Automatic reply", "away", headers={"Auto-Submitted": "auto-replied"})

    msg = provider.get_message(mid)

    assert msg == {"provider_message_id": mid, "thread_id": "conv-9", "from_email": "dave@acme.co.uk",
                   "subject": "Re: old quotes", "body": "Yes call me",
                   "internal_date_ms": int(received.timestamp() * 1000), "auto_submitted": False}
    assert provider.get_message(auto)["auto_submitted"] is True
    get = [c for c in graph.calls if c["method"] == "GET"][0]
    assert "ImmutableId" in get["headers"]["Prefer"] and "internetMessageHeaders" in get["params"]["$select"]


def test_outlook_bounce_notice_is_matched_by_the_classifier():
    """Exchange NDRs come from postmaster@ with an 'Undeliverable:' subject."""
    from outreach.reply_classifier.classify import categorize_reply
    verdict = categorize_reply("postmaster@velarqomail.com", "Undeliverable: old quotes",
                               "Your message to info@acme.co.uk couldn't be delivered. 550 5.1.1 user unknown")
    assert verdict["category"] == "bounce" and verdict["suppress"]
