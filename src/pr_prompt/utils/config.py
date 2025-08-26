from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from tomllib import TOMLDecodeError


@dataclass
class PrPromptConfig:
    """Configuration for pr-prompt tool."""

    blacklist_patterns: list[str] = field(default_factory=lambda: ["*.lock"])
    context_patterns: list[str] = field(default_factory=lambda: ["LLM.md"])


def load_config() -> PrPromptConfig:
    """Load configuration from pyproject.toml."""
    pyproject_path = find_pyproject_path()

    default_config = PrPromptConfig()

    if not pyproject_path.exists():
        return PrPromptConfig()

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)

        pr_prompt_config = data.get("tool", {}).get("pr-prompt", {})

        return PrPromptConfig(
            blacklist_patterns=pr_prompt_config.get(
                "blacklist_patterns", default_config.blacklist_patterns
            ),
            context_patterns=pr_prompt_config.get(
                "context_patterns", default_config.context_patterns
            ),
        )
    except TOMLDecodeError:
        return PrPromptConfig()


def find_pyproject_path() -> Path:
    config_path = Path.cwd()
    while config_path != config_path.parent:
        pyproject_path = config_path / "pyproject.toml"
        if pyproject_path.exists():
            config_path = pyproject_path
            break
        config_path = config_path.parent
    else:
        config_path = Path("pyproject.toml")
    return config_path
