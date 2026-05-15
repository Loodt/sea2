"""Provider detection + config tests."""

from __future__ import annotations

import pytest

from sea2.providers import (
    PROVIDERS,
    conductor_file,
    conductor_file_candidates,
    detect_provider,
)

ENV_VARS = ("SEA_PROVIDER", "CODEX_CLI", "CODEX", "CLAUDECODE")


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for v in ENV_VARS:
        monkeypatch.delenv(v, raising=False)


def test_default_is_claude() -> None:
    assert detect_provider() == "claude"


def test_explicit_sea_provider_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("SEA_PROVIDER", "codex-local")
    assert detect_provider() == "codex-local"


def test_unknown_sea_provider_falls_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEA_PROVIDER", "bogus")
    monkeypatch.setenv("CLAUDECODE", "1")
    assert detect_provider() == "claude"


def test_codex_env_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_CLI", "1")
    assert detect_provider() == "codex"


def test_claudecode_env_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDECODE", "1")
    assert detect_provider() == "claude"


def test_all_providers_have_instruction_files() -> None:
    for p, cfg in PROVIDERS.items():
        assert cfg.instruction_file in {"CLAUDE.md", "AGENTS.md"}, p


def test_anthropic_sdk_provider_registered() -> None:
    assert "anthropic-sdk" in PROVIDERS


def test_conductor_file_candidates_dedupes_and_preferred_first() -> None:
    cands = conductor_file_candidates("codex")
    assert cands[0] == "AGENTS.md"
    assert len(cands) == len(set(cands))


def test_conductor_file_default() -> None:
    assert conductor_file() == "CLAUDE.md"
