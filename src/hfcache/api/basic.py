"""One protected Basic administrator and bounded independent Argon2id work."""

import asyncio
import base64
import binascii
import hmac
import json
import os
import re
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from threading import Lock
from typing import TYPE_CHECKING, Annotated, Literal

from cryptography.exceptions import InvalidKey, UnsupportedAlgorithm
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from pydantic import BeforeValidator, ConfigDict, Field, field_validator

from hfcache.api.auth import AdminCapability, AuthenticationMethod, CredentialClass, Principal
from hfcache.api.credential_sources import invalid_credential, read_protected_bytes, source_path
from hfcache.errors import AuthenticationCapacityError, AuthenticationError, SafetyError
from hfcache.models import DurableModel

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from concurrent.futures import Future

    from hfcache.server_config import BasicConfig

MAXIMUM_RECORD_BYTES = 8192
MAXIMUM_AUTHORIZATION_BYTES = 8192
MAXIMUM_USERNAME_BYTES = 128
MAXIMUM_PASSWORD_BYTES = 1024
_SUBJECT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_PHC_PREFIX = "$argon2id$v=19$m=65536,t=3,p=1$"
_ACTIVE = 2
_WAITING = 8
_FAILURES = 30
_WINDOW = 60.0


def _schema(value: object) -> int:
    if type(value) is not int or value != 1:
        message = "administrator record schema must be integer 1"
        raise ValueError(message)
    return value


def _subject(value: str) -> str:
    if not isinstance(value, str) or not _SUBJECT.fullmatch(value):
        message = "administrator subject has invalid grammar"
        raise ValueError(message)
    return value


def _username(value: str) -> str:
    if not isinstance(value, str):
        message = "administrator username has invalid shape"
        raise TypeError(message)
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        message = "administrator username is not valid UTF-8"
        raise ValueError(message) from None
    if (
        not value
        or not value.isprintable()
        or ":" in value
        or len(encoded) > MAXIMUM_USERNAME_BYTES
    ):
        message = "administrator username has invalid shape"
        raise ValueError(message)
    return value


def _password(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) > MAXIMUM_PASSWORD_BYTES:
        message = "password must be bounded UTF-8 bytes"
        raise ValueError(message)
    try:
        value.decode("utf-8")
    except UnicodeError:
        message = "password must be bounded UTF-8 bytes"
        raise ValueError(message) from None
    return value


def _decode_phc_part(value: str, size: int) -> bytes:
    try:
        decoded = base64.b64decode(value + "=" * (-len(value) % 4), validate=True)
    except ValueError, binascii.Error:
        message = "administrator password hash encoding is invalid"
        raise ValueError(message) from None
    if len(decoded) != size or base64.b64encode(decoded).decode("ascii").rstrip("=") != value:
        message = "administrator password hash encoding is invalid"
        raise ValueError(message)
    return decoded


def _phc(value: str) -> str:
    if not value.isascii() or not value.startswith(_PHC_PREFIX):
        message = "administrator password hash parameters are invalid"
        raise ValueError(message)
    salt, password_hash = value[len(_PHC_PREFIX) :].split("$")
    _decode_phc_part(salt, 16)
    _decode_phc_part(password_hash, 32)
    return value


class ProtectedAdministratorRecord(DurableModel):
    """Only an immutable password hash is serializable; a password is never stored."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Annotated[Literal[1], BeforeValidator(_schema)]
    subject: str
    username: str
    password_hash: str = Field(repr=False, max_length=128)

    _valid_subject = field_validator("subject")(_subject)
    _valid_username = field_validator("username")(_username)
    _valid_phc = field_validator("password_hash")(_phc)


def create_administrator_record(
    subject: str, username: str, password: bytes
) -> ProtectedAdministratorRecord:
    """Derive one fixed-profile hash from protected in-memory provisioning input."""
    try:
        _subject(subject)
        _username(username)
        _password(password)
        password_hash = Argon2id(
            salt=os.urandom(16), length=32, iterations=3, lanes=1, memory_cost=65536
        ).derive_phc_encoded(password)
        return ProtectedAdministratorRecord(
            schema_version=1, subject=subject, username=username, password_hash=password_hash
        )
    except ValueError, TypeError, UnsupportedAlgorithm, MemoryError:
        raise invalid_credential() from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            message = "duplicate administrator record field"
            raise ValueError(message)
        result[key] = value
    return result


def load_basic_provider(
    config: BasicConfig | None, *, environ: Mapping[str, str] | None = None
) -> BasicProvider | None:
    """Disabled configuration performs no source access; enabled failures refuse startup."""
    if config is None:
        return None
    environment = os.environ if environ is None else environ
    raw = read_protected_bytes(source_path(config.administrator, environment), MAXIMUM_RECORD_BYTES)
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        record = ProtectedAdministratorRecord.model_validate(payload)
        return BasicProvider(record)
    except ValueError, TypeError, RecursionError:
        raise invalid_credential() from None


def _decoded_credentials(encoded: str) -> tuple[bytes, bytes]:
    raw = base64.b64decode(encoded, validate=True)
    if base64.b64encode(raw).decode("ascii") != encoded:
        message = "noncanonical Basic credential encoding"
        raise ValueError(message)
    username, separator, password = raw.partition(b":")
    if not separator or len(username) > MAXIMUM_USERNAME_BYTES:
        message = "invalid Basic credential shape"
        raise ValueError(message)
    _username(username.decode("utf-8"))
    _password(password)
    return username, password


def _credentials(authorization: str) -> tuple[bytes, bytes]:
    if (
        not isinstance(authorization, str)
        or not authorization.isascii()
        or len(authorization) > MAXIMUM_AUTHORIZATION_BYTES
    ):
        raise AuthenticationError
    scheme, separator, encoded = authorization.partition(" ")
    if scheme.lower() != "basic" or separator != " " or not encoded:
        raise AuthenticationError
    try:
        return _decoded_credentials(encoded)
    except ValueError, TypeError, UnicodeError, binascii.Error:
        raise AuthenticationError from None


def _unavailable() -> SafetyError:
    return SafetyError.single("authentication service is unavailable or draining", code="HFAPI009")


class _Outcome(Enum):
    ACCEPTED = auto()
    DENIED = auto()
    THROTTLED = auto()
    UNAVAILABLE = auto()


@dataclass(frozen=True, slots=True)
class AuthPoolSnapshot:
    active: int
    waiting: int
    failures: int
    reservations: int
    accepting: bool


class _AttemptBudget:
    def __init__(self, monotonic: Callable[[], float]) -> None:
        self.monotonic = monotonic
        self.lock = Lock()
        self.failures: deque[float] = deque(maxlen=_FAILURES)
        self.reservations = 0

    def _prune(self) -> None:
        boundary = self.monotonic() - _WINDOW
        while self.failures and self.failures[0] <= boundary:
            self.failures.popleft()

    def available(self, *, reserve: bool = False) -> bool:
        with self.lock:
            self._prune()
            if len(self.failures) + self.reservations >= _FAILURES:
                return False
            if reserve:
                self.reservations += 1
            return True

    def complete(self, *, accepted: bool) -> None:
        with self.lock:
            self._prune()
            self.reservations -= 1
            if not accepted:
                self.failures.append(self.monotonic())

    def snapshot(self) -> tuple[int, int]:
        with self.lock:
            self._prune()
            return len(self.failures), self.reservations


@dataclass(slots=True)
class _Job:
    password: bytes = field(repr=False)
    username_matches: bool
    result: asyncio.Future[_Outcome] = field(repr=False)


class BasicProvider:
    """Own exactly two hash workers, eight waiting requests and a global failure budget."""

    def __init__(
        self,
        record: ProtectedAdministratorRecord,
        *,
        verify: Callable[[bytes], bool] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        # Public construction must not bypass strict protected-record validation.
        self._record = ProtectedAdministratorRecord.model_validate(record.model_dump())
        try:
            salt = _decode_phc_part(
                self._record.password_hash[len(_PHC_PREFIX) :].split("$")[0], 16
            )
            Argon2id(salt=salt, length=32, iterations=3, lanes=1, memory_cost=65536)
        except ValueError, UnsupportedAlgorithm, MemoryError:
            raise invalid_credential() from None
        self._verify = verify or self._verify_password
        self._budget = _AttemptBudget(monotonic)
        self._executor = ThreadPoolExecutor(max_workers=_ACTIVE, thread_name_prefix="hfcache-auth")
        self._active: dict[Future[_Outcome], _Job] = {}
        self._waiting: deque[_Job] = deque()
        self._accepting = True
        self._loop: asyncio.AbstractEventLoop | None = None
        self._drained: asyncio.Event | None = None
        self._closing: asyncio.Task[None] | None = None

    @property
    def subject(self) -> str:
        return self._record.subject

    @property
    def username(self) -> str:
        return self._record.username

    @property
    def stats(self) -> AuthPoolSnapshot:
        failures, reservations = self._budget.snapshot()
        return AuthPoolSnapshot(
            len(self._active), len(self._waiting), failures, reservations, self._accepting
        )

    def _owner_loop(self) -> asyncio.AbstractEventLoop:
        loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = loop
            self._drained = asyncio.Event()
            self._drained.set()
        elif self._loop is not loop:
            raise _unavailable()
        return loop

    def _verify_password(self, password: bytes) -> bool:
        try:
            Argon2id.verify_phc_encoded(password, self._record.password_hash)
        except InvalidKey:
            return False
        return True

    def _work(self, job: _Job) -> _Outcome:
        if not self._budget.available(reserve=True):
            return _Outcome.THROTTLED
        accepted = False
        try:
            valid = self._verify(job.password)
        except Exception:  # noqa: BLE001 - worker failures never expose verifier input or traces
            return _Outcome.UNAVAILABLE
        else:
            if type(valid) is not bool:
                return _Outcome.UNAVAILABLE
            accepted = valid and job.username_matches
            return _Outcome.ACCEPTED if accepted else _Outcome.DENIED
        finally:
            self._budget.complete(accepted=accepted)

    def _dispatch(self, job: _Job) -> None:
        try:
            future = self._executor.submit(self._work, job)
        except Exception:  # noqa: BLE001 - executor admission failure must retire the unsubmitted job
            job.password = b""
            job.result.set_result(_Outcome.UNAVAILABLE)
            return
        self._active[future] = job
        loop = self._owner_loop()
        future.add_done_callback(lambda done: loop.call_soon_threadsafe(self._finished, done))

    def _finished(self, future: Future[_Outcome]) -> None:
        job = self._active.pop(future)
        job.password = b""
        try:
            outcome = future.result()
        except BaseException:  # noqa: BLE001 - every completed owned worker must retire its capacity
            outcome = _Outcome.UNAVAILABLE
        if not job.result.done():
            job.result.set_result(outcome)
        while self._waiting and len(self._active) < _ACTIVE:
            self._dispatch(self._waiting.popleft())
        if not self._active and not self._waiting and self._drained is not None:
            self._drained.set()

    async def authenticate(self, authorization: str) -> Principal:
        username, password = _credentials(authorization)
        loop = self._owner_loop()
        if not self._accepting:
            raise _unavailable()
        if not self._budget.available() or (
            len(self._active) == _ACTIVE and len(self._waiting) == _WAITING
        ):
            raise AuthenticationCapacityError
        job = _Job(
            password,
            hmac.compare_digest(username, self.username.encode("utf-8")),
            loop.create_future(),
        )
        if self._drained is not None:
            self._drained.clear()
        if len(self._active) < _ACTIVE:
            self._dispatch(job)
            if not self._active and self._drained is not None:
                self._drained.set()
        else:
            self._waiting.append(job)
        outcome = await asyncio.shield(job.result)
        if outcome is _Outcome.THROTTLED:
            raise AuthenticationCapacityError
        if outcome is _Outcome.UNAVAILABLE:
            raise _unavailable()
        if outcome is _Outcome.DENIED:
            raise AuthenticationError
        return Principal(
            CredentialClass.REST_WRITER,
            authentication_method=AuthenticationMethod.BASIC,
            subject=self.subject,
            admin_capabilities=frozenset(AdminCapability),
        )

    def stop_admission(self) -> None:
        self._accepting = False

    async def _join(self) -> None:
        if self._drained is not None:
            await self._drained.wait()
        await asyncio.to_thread(self._executor.shutdown, wait=True, cancel_futures=False)

    async def aclose(self) -> None:
        self.stop_admission()
        self._owner_loop()
        if self._closing is None:
            self._closing = asyncio.create_task(self._join())
        cancelled = False
        while not self._closing.done():
            try:
                await asyncio.shield(self._closing)
            except asyncio.CancelledError:
                cancelled = True
        self._closing.result()
        if cancelled:
            raise asyncio.CancelledError
