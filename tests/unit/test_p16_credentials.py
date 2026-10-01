"""P16 credential boundary unit tests (D07): references are opaque, values redacted."""

from __future__ import annotations

import pytest

from core.agent import AgentRuntimeError, ErrorCode
from services.ai.credentials import EnvSecretResolver, SecretValue

def test_env_reference_resolves_without_exposing_value() -> None:
    resolver = EnvSecretResolver({"OPENAI_API_KEY": "sk-secret-value"})
    secret = resolver.resolve("env:OPENAI_API_KEY")
    assert secret.reveal() == "sk-secret-value"
    assert "sk-secret-value" not in repr(secret)
    assert "sk-secret-value" not in str(secret)


def test_missing_credential_fails_closed() -> None:
    with pytest.raises(AgentRuntimeError) as exc:
        EnvSecretResolver({}).resolve("env:OPENAI_API_KEY")
    assert exc.value.code == ErrorCode.CREDENTIAL_UNAVAILABLE
    assert "OPENAI_API_KEY" not in str(exc.value)


def test_non_env_reference_is_rejected_and_not_echoed() -> None:
    with pytest.raises(AgentRuntimeError) as exc:
        EnvSecretResolver({}).resolve("vault:secret/data/key")
    assert exc.value.code == ErrorCode.CREDENTIAL_UNAVAILABLE
    assert "vault" not in str(exc.value)


def test_secret_value_never_stringifies_material() -> None:
    value = SecretValue("top-secret-material", "env:X")
    assert "top-secret-material" not in f"{value!r}"
    assert "top-secret-material" not in f"{value}"
