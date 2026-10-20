"""Deterministic worker completion, queue, failure-budget and shutdown proofs."""

import asyncio
import base64
import secrets
import threading
from typing import cast

import pytest

from hfcache.api.basic import BasicProvider, create_administrator_record
from hfcache.errors import AuthenticationCapacityError, AuthenticationError, SafetyError


@pytest.fixture(scope="module")
def record():
    return create_administrator_record("human:pool", "operator", secrets.token_urlsafe(32).encode())


def authorization():
    password = secrets.token_urlsafe(32).encode()
    return "Basic " + base64.b64encode(b"operator:" + password).decode()


async def until(predicate):
    async with asyncio.timeout(5):
        while not predicate():
            await asyncio.sleep(0.001)


def test_two_actual_workers_eight_explicit_waiters_and_cancelled_observers_keep_slots(record):
    release = threading.Event()
    lock = threading.Lock()
    calls = 0
    active = 0
    maximum = 0

    def verify(password):
        nonlocal calls, active, maximum
        with lock:
            calls += 1
            active += 1
            maximum = max(maximum, active)
        try:
            assert release.wait(5)
            return True
        finally:
            with lock:
                active -= 1

    async def exercise():
        provider = BasicProvider(record, verify=verify)
        tasks = [asyncio.create_task(provider.authenticate(authorization())) for _ in range(10)]
        try:
            await until(
                lambda: (
                    provider.stats.active == 2
                    and provider.stats.waiting == 8
                    and provider.stats.reservations == 2
                )
            )
            with pytest.raises(AuthenticationCapacityError) as failure:
                await provider.authenticate(authorization())
            assert failure.value.status_code == 429
            assert failure.value.exit_code == 20
            tasks[0].cancel()
            tasks[2].cancel()
            await asyncio.gather(tasks[0], tasks[2], return_exceptions=True)
            assert provider.stats.active == 2
            assert provider.stats.waiting == 8
            assert calls == 2
            release.set()
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            await until(lambda: provider.stats.active == provider.stats.waiting == 0)
            assert sum(isinstance(outcome, asyncio.CancelledError) for outcome in outcomes) == 2
            assert calls == 10
            assert maximum == 2
            assert provider.stats.failures == provider.stats.reservations == 0
        finally:
            release.set()
            await asyncio.gather(*tasks, return_exceptions=True)
            await provider.aclose()
        assert all(not worker.is_alive() for worker in provider._executor._threads)

    asyncio.run(exercise())


def test_failure_reservations_and_queued_start_recheck_allow_no_thirty_first_hash(record):
    now = [100.0]
    release = threading.Event()
    lock = threading.Lock()
    calls = 0

    def verify(password):
        nonlocal calls
        with lock:
            calls += 1
            count = calls
        if count > 27:
            assert release.wait(5)
        return False

    async def exercise():
        provider = BasicProvider(record, verify=verify, monotonic=lambda: now[0])
        tasks = []
        try:
            for _ in range(27):
                with pytest.raises(AuthenticationError):
                    await provider.authenticate(authorization())
            assert provider.stats.failures == 27
            tasks = [asyncio.create_task(provider.authenticate(authorization())) for _ in range(10)]
            await until(lambda: provider.stats.waiting == 8 and provider.stats.reservations == 2)
            assert calls == 29
            release.set()
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            assert sum(isinstance(outcome, AuthenticationError) for outcome in outcomes) == 3
            assert (
                sum(isinstance(outcome, AuthenticationCapacityError) for outcome in outcomes) == 7
            )
            assert calls == 30
            assert provider.stats.failures == 30
            assert provider.stats.reservations == 0
            with pytest.raises(AuthenticationCapacityError):
                await provider.authenticate(authorization())
            assert calls == 30
            now[0] = 159.999
            with pytest.raises(AuthenticationCapacityError):
                await provider.authenticate(authorization())
            now[0] = 160.0
            with pytest.raises(AuthenticationError):
                await provider.authenticate(authorization())
            assert calls == 31
            assert provider.stats.failures == 1
        finally:
            release.set()
            await asyncio.gather(*tasks, return_exceptions=True)
            await provider.aclose()

    asyncio.run(exercise())


def test_two_simultaneous_final_reservations_throttle_new_work_before_queue(record):
    release = threading.Event()
    calls = 0
    lock = threading.Lock()

    def verify(password):
        nonlocal calls
        with lock:
            calls += 1
            count = calls
        if count > 28:
            assert release.wait(5)
        return False

    async def exercise():
        provider = BasicProvider(record, verify=verify)
        tasks = []
        try:
            for _ in range(28):
                with pytest.raises(AuthenticationError):
                    await provider.authenticate(authorization())
            tasks = [asyncio.create_task(provider.authenticate(authorization())) for _ in range(2)]
            await until(lambda: provider.stats.reservations == 2)
            assert provider.stats.failures == 28
            with pytest.raises(AuthenticationCapacityError):
                await provider.authenticate(authorization())
            assert provider.stats.waiting == 0
            assert calls == 30
        finally:
            release.set()
            await asyncio.gather(*tasks, return_exceptions=True)
            await provider.aclose()
        assert provider.stats.failures == 30

    asyncio.run(exercise())


def test_successes_do_not_spend_the_failure_budget(record):
    async def exercise():
        provider = BasicProvider(record, verify=lambda _: True)
        try:
            for _ in range(50):
                await provider.authenticate(authorization())
            assert provider.stats.failures == provider.stats.reservations == 0
        finally:
            await provider.aclose()

    asyncio.run(exercise())


@pytest.mark.parametrize("behavior", ["exception", "nonboolean"])
def test_verifier_failures_are_safe_unavailable_and_retire_all_capacity(record, behavior):
    def verify(password):
        if behavior == "exception":
            raise RuntimeError(password.decode())
        return cast("bool", None)

    async def exercise():
        provider = BasicProvider(record, verify=verify)
        try:
            with pytest.raises(SafetyError) as failure:
                await provider.authenticate(authorization())
            assert failure.value.problems[0].code == "HFAPI009"
            assert (
                provider.stats.active == provider.stats.waiting == provider.stats.reservations == 0
            )
            assert provider.stats.failures == 1
        finally:
            await provider.aclose()

    asyncio.run(exercise())


@pytest.mark.parametrize("error", [RuntimeError, MemoryError])
def test_executor_submit_failure_rolls_back_without_a_reservation(record, monkeypatch, error):
    async def exercise():
        provider = BasicProvider(record, verify=lambda _: True)

        def unavailable(*args, **kwargs):
            raise error

        monkeypatch.setattr(provider._executor, "submit", unavailable)
        try:
            with pytest.raises(SafetyError):
                await provider.authenticate(authorization())
            assert (
                provider.stats.active == provider.stats.waiting == provider.stats.reservations == 0
            )
            assert provider.stats.failures == 0
        finally:
            await provider.aclose()

    asyncio.run(exercise())


def test_cancelled_close_still_drains_waiters_and_joins_exact_workers(record):
    release = threading.Event()

    def verify(password):
        assert release.wait(5)
        return True

    async def exercise():
        provider = BasicProvider(record, verify=verify)
        tasks = [asyncio.create_task(provider.authenticate(authorization())) for _ in range(4)]
        closing = None
        try:
            await until(lambda: provider.stats.active == provider.stats.waiting == 2)
            closing = asyncio.create_task(provider.aclose())
            await until(lambda: not provider.stats.accepting)
            closing.cancel()
            await asyncio.sleep(0)
            assert not closing.done()
            with pytest.raises(SafetyError):
                await provider.authenticate(authorization())
            assert provider.stats.active == provider.stats.waiting == 2
            release.set()
            await asyncio.gather(*tasks)
            with pytest.raises(asyncio.CancelledError):
                await closing
            assert (
                provider.stats.active == provider.stats.waiting == provider.stats.reservations == 0
            )
            assert all(not worker.is_alive() for worker in provider._executor._threads)
            await provider.aclose()
        finally:
            release.set()
            await asyncio.gather(*tasks, return_exceptions=True)
            if closing is not None:
                await asyncio.gather(closing, return_exceptions=True)
            await provider.aclose()

    asyncio.run(exercise())


def test_closing_without_requests_starts_no_hash_worker(record):
    async def exercise():
        provider = BasicProvider(record, verify=lambda _: pytest.fail("close hashed a password"))
        await provider.aclose()
        assert not provider._executor._threads
        assert not provider.stats.accepting

    asyncio.run(exercise())
