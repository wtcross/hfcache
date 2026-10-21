"""Real ASGI send backpressure/cancellation; no socket or Caddy acceptance claim."""

import asyncio

import pytest

from hfcache.api import ui_serving
from hfcache.api.ui_serving import UiResponse, UiStreams
from hfcache.errors import SafetyError


def test_sixteen_stalled_headers_have_no_seventeenth_waiter_and_head_needs_no_slot():
    async def exercise():
        streams = UiStreams()
        response = UiResponse(
            b"x" * 200000, mime="text/javascript", policy="ui_asset_private", streams=streams
        )
        release = asyncio.Event()
        never = asyncio.Event()
        entered = asyncio.Event()
        count = 0
        chunks = []

        async def send(message):
            nonlocal count
            if message["type"] == "http.response.start":
                count += 1
                if count == 16:
                    entered.set()
                await release.wait()
            else:
                chunks.append(len(message.get("body", b"")))

        async def receive():
            await never.wait()
            return {"type": "http.disconnect"}

        tasks = [asyncio.create_task(response({"method": "GET"}, receive, send)) for _ in range(16)]
        await asyncio.wait_for(entered.wait(), 2)
        assert streams.active == 16
        assert len(streams.tasks) == 32
        assert {task.get_name() for task in streams.tasks} == {
            "hfcache-ui-send",
            "hfcache-ui-disconnect",
        }
        with pytest.raises(SafetyError, match="full or draining"):
            await response({"method": "GET"}, receive, send)
        head = []

        async def send_head(message):
            head.append(message)

        await response({"method": "HEAD"}, receive, send_head)
        assert head[-1]["body"] == b""
        assert (b"content-length", b"200000") in head[0]["headers"]
        assert streams.active == 16
        closing = asyncio.create_task(streams.aclose())
        await asyncio.sleep(0)
        assert not closing.done()
        release.set()
        await asyncio.wait_for(asyncio.gather(*tasks), 2)
        await asyncio.wait_for(closing, 2)
        assert streams.active == 0
        assert not streams.tasks
        assert not streams.accepting
        assert chunks
        assert max(chunks) <= 65536

    asyncio.run(exercise())


@pytest.mark.parametrize("phase", ["start", "body"])
def test_absolute_send_deadline_retires_the_lease_and_both_owned_tasks(monkeypatch, phase):
    monkeypatch.setattr(ui_serving, "STREAM_DEADLINE_SECONDS", 0.02)

    async def exercise():
        streams = UiStreams()
        response = UiResponse(b"bounded", mime="text/html", policy="ui_document", streams=streams)
        blocked = asyncio.Event()
        before = set(asyncio.all_tasks())

        async def send(message):
            if message["type"] == "http.response." + phase:
                await blocked.wait()

        async def receive():
            await blocked.wait()
            return {"type": "http.disconnect"}

        with pytest.raises(TimeoutError):
            await response({"method": "GET"}, receive, send)
        assert streams.active == 0
        assert not streams.tasks
        await streams.aclose()
        assert set(asyncio.all_tasks()) == before

    asyncio.run(exercise())


@pytest.mark.parametrize("failure", ["disconnect", "oserror", "cancel"])
def test_actual_disconnect_send_failure_and_request_cancellation_release_once(failure):
    async def exercise():
        streams = UiStreams()
        response = UiResponse(b"body", mime="text/html", policy="ui_document", streams=streams)
        entered = asyncio.Event()
        disconnected = asyncio.Event()
        held = asyncio.Event()

        async def send(message):
            if message["type"] == "http.response.body":
                entered.set()
                if failure == "oserror":
                    message = "owned broken transport"
                    raise OSError(message)
                await held.wait()

        async def receive():
            await disconnected.wait()
            return {"type": "http.disconnect"}

        task = asyncio.create_task(response({"method": "GET"}, receive, send))
        await asyncio.wait_for(entered.wait(), 2)
        if failure == "disconnect":
            disconnected.set()
            await asyncio.wait_for(task, 2)
        elif failure == "cancel":
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            with pytest.raises(OSError, match="owned broken transport"):
                await task
        assert streams.active == 0
        lease = streams.acquire()
        lease.release()
        lease.release()
        assert streams.active == 0
        await streams.aclose()

    asyncio.run(exercise())


def test_repeated_cancellation_holds_capacity_until_owned_observer_actually_finishes():
    async def exercise():
        streams = UiStreams()
        entered = asyncio.Event()
        observer_cancelled = asyncio.Event()
        release = asyncio.Event()

        async def send(_message):
            entered.set()
            await release.wait()

        async def receive():
            try:
                await release.wait()
            except asyncio.CancelledError:
                observer_cancelled.set()
                await release.wait()
            return {"type": "http.disconnect"}

        response = UiResponse(b"body", mime="text/html", policy="ui_document", streams=streams)
        request = asyncio.create_task(response({"method": "GET"}, receive, send))
        await asyncio.wait_for(entered.wait(), 2)
        request.cancel()
        await asyncio.wait_for(observer_cancelled.wait(), 2)
        request.cancel()
        await asyncio.sleep(0)
        assert not request.done()
        assert streams.active == 1
        assert len(streams.tasks) == 2
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(request, 2)
        assert streams.active == 0
        assert not streams.tasks
        await streams.aclose()

    asyncio.run(exercise())
