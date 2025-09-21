import sys
from pathlib import Path

from .errors import InvalidConfigError

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]


def load_toml_config() -> dict:
    toml_path = find_toml_file_path()
    if not toml_path.exists():
        return {}

    toml_config = load_config_toml(toml_path)
    pr_prompt_config = get_pr_prompt_config(toml_config)
    validate_toml_config(pr_prompt_config)
    return pr_prompt_config


def find_toml_file_path() -> Path:
    config_path = Path.cwd()
    while config_path != config_path.parent:
        # Check for pr_prompt.toml first (higher priority)
        for filename in ["pr_prompt.toml", "pyproject.toml"]:
            candidate = config_path / filename
            if candidate.exists():
                return candidate
        config_path = config_path.parent
    return Path("pr_prompt.toml")


def load_config_toml(config_path: Path) -> dict[str, dict]:
    try:
        with config_path.open("rb") as f:
            return tomllib.load(f)

    except tomllib.TOMLDecodeError:
        return {}


def get_pr_prompt_config(config_toml: dict) -> dict:
    return config_toml.get("tool", {}).get("pr-prompt", {})


def validate_toml_config(config: dict) -> None:
    """Validate TOML configuration values and raise error if invalid."""
    validators = {
        "blacklist_patterns": lambda x: isinstance(x, list)
        and all(isinstance(p, str) for p in x),
        "context_patterns": lambda x: isinstance(x, list)
        and all(isinstance(p, str) for p in x),
        "diff_context_lines": lambda x: isinstance(x, int) and x >= 0,
        "include_commit_messages": lambda x: isinstance(x, bool),
        "repo_path": lambda x: isinstance(x, str),
        "remote": lambda x: isinstance(x, str),
        "custom_instructions": lambda x: isinstance(x, str),
        "default_base_branch": lambda x: isinstance(x, str),
        "fetch_base": lambda x: isinstance(x, bool),
    }

    for field, value in config.items():
        if field not in validators:
            msg = f"Unknown config field '{field}' in [tool.pr-prompt]"
            raise InvalidConfigError(msg)

        if not validators[field](value):
            msg = f"Invalid config for '{field}': {value}"
            raise InvalidConfigError(msg)
