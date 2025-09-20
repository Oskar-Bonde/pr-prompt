from pathlib import Path

import tomllib
from tomllib import TOMLDecodeError


def load_toml_config() -> dict:
    toml_path = find_toml_file_path()
    if not toml_path.exists():
        return {}

    toml_config = load_config_toml(toml_path)
    return get_pr_prompt_config(toml_config, toml_path.name)


def find_toml_file_path() -> Path:
    config_path = Path.cwd()
    while config_path != config_path.parent:
        # Check for pr_prompt.toml first
        pr_prompt_path = config_path / "pr_prompt.toml"
        if pr_prompt_path.exists():
            return pr_prompt_path

        # Fall back to pyproject.toml
        pyproject_path = config_path / "pyproject.toml"
        if pyproject_path.exists():
            return pyproject_path

        config_path = config_path.parent
    return Path("pr_prompt.toml")


def load_config_toml(config_path: Path) -> dict[str, dict]:
    try:
        with config_path.open("rb") as f:
            return tomllib.load(f)

    except TOMLDecodeError:
        return {}


def get_pr_prompt_config(config_toml: dict) -> dict:
    return config_toml.get("tool", {}).get("pr-prompt", {})
