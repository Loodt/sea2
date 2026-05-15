"""Provider abstraction.

Port of `sea/src/types.ts:1-79` with a fourth provider added: `anthropic-sdk`
for direct SDK calls. Tier 2 cross-family verification must not round-trip
through the Claude Code CLI (commitment 3: isolated cross-family verifier),
so we ship a native SDK path from the start.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Literal

Provider = Literal["claude", "codex", "codex-local", "anthropic-sdk"]


@dataclass(frozen=True)
class ProviderConfig:
    binary: str
    base_args: tuple[str, ...] = field(default_factory=tuple)
    model_flag: str = "--model"
    # Auto-discovered conductor filename for this provider (CLAUDE.md vs AGENTS.md).
    instruction_file: str = "CLAUDE.md"


def _codex_binary() -> str:
    return "codex.cmd" if sys.platform == "win32" else "codex"


PROVIDERS: dict[Provider, ProviderConfig] = {
    "claude": ProviderConfig(
        binary="claude",
        base_args=("-p", "--output-format", "text", "--dangerously-skip-permissions"),
        model_flag="--model",
        instruction_file="CLAUDE.md",
    ),
    "codex": ProviderConfig(
        binary=_codex_binary(),
        base_args=("-a", "never", "--search", "exec", "-", "--color", "never"),
        model_flag="--model",
        instruction_file="AGENTS.md",
    ),
    "codex-local": ProviderConfig(
        # Approval/sandbox configured in $CODEX_HOME/config.toml; `--oss` must
        # follow `exec` to be honored.
        binary=_codex_binary(),
        base_args=(
            "exec",
            "--oss",
            "--local-provider",
            "ollama",
            "-m",
            "llama3.1:8b-instruct-q4_K_M",
            "--skip-git-repo-check",
            "--color",
            "never",
            "-",
        ),
        model_flag="--model",
        instruction_file="AGENTS.md",
    ),
    # Direct Anthropic SDK. No `binary` is launched — the SDK is invoked
    # in-process. Tier 2 verifier path; never use this for default execution.
    "anthropic-sdk": ProviderConfig(
        binary="anthropic-sdk",
        base_args=(),
        model_flag="--model",
        instruction_file="CLAUDE.md",
    ),
}


def detect_provider() -> Provider:
    """Auto-detect the active provider from harness env vars.

    Priority:
      1. SEA_PROVIDER env var (explicit override).
      2. CODEX_CLI=1 / CODEX=1 → codex.
      3. CLAUDECODE=1 → claude.
      4. Default: claude.
    """
    override = os.environ.get("SEA_PROVIDER")
    if override and override in PROVIDERS:
        return override
    if os.environ.get("CODEX_CLI") == "1" or os.environ.get("CODEX") == "1":
        return "codex"
    if os.environ.get("CLAUDECODE") == "1":
        return "claude"
    return "claude"


def conductor_file(provider: Provider | None = None) -> str:
    return PROVIDERS[provider or "claude"].instruction_file


def conductor_file_candidates(provider: Provider | None = None) -> list[str]:
    preferred = conductor_file(provider)
    seen: set[str] = {preferred}
    out: list[str] = [preferred]
    for cfg in PROVIDERS.values():
        if cfg.instruction_file not in seen:
            seen.add(cfg.instruction_file)
            out.append(cfg.instruction_file)
    return out


__all__ = [
    "PROVIDERS",
    "Provider",
    "ProviderConfig",
    "conductor_file",
    "conductor_file_candidates",
    "detect_provider",
]
