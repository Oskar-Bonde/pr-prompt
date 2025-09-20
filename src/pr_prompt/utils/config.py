from pathlib import Path

import tomllib
from tomllib import TOMLDecodeError


def load_toml_config() -> dict:
    pyproject_toml_path = find_pyproject_toml_path()
    if not pyproject_toml_path.exists():
        return {}

    pyproject_toml = load_pyproject_toml(pyproject_toml_path)
    return get_pr_prompt_config(pyproject_toml)


def find_pyproject_toml_path() -> Path:
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


def load_pyproject_toml(pyproject_path: Path) -> dict[str, dict]:
    try:
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)

    except TOMLDecodeError:
        return {}


def get_pr_prompt_config(pyproject_toml: dict) -> dict:
    return pyproject_toml.get("tool", {}).get("pr-prompt", {})
