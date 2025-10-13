from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Callable

import typer
from rich.console import Console

from . import __version__
from .generator import PrPromptGenerator

app = typer.Typer(
    help="Generate structured prompts for pull requests.",
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        console.print(f"pr-prompt version {__version__}")
        raise typer.Exit


class PromptType(str, Enum):
    REVIEW = "review"
    DESCRIPTION = "description"
    CUSTOM = "custom"


@app.command()
def generate(
    prompt_type: Annotated[
        PromptType,
        typer.Argument(
            help="Type of prompt to generate",
            case_sensitive=False,
        ),
    ] = PromptType.REVIEW,
    base_ref: Annotated[
        str | None,
        typer.Option(
            "--base-ref",
            "-b",
            help="The branch/commit to compare against (e.g., 'origin/main'). Infer from default branch if not provided.",
        ),
    ] = None,
    write: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--write",
            help="Write to .pr_prompt/<type>_<timestamp>.md instead of stdout. Timestamp: UTC 'YYYY-MM-DD_HH-MM-SS'.",
        ),
    ] = False,
    blacklist: Annotated[
        list[str] | None,
        typer.Option(
            "--blacklist",
            help="File patterns to exclude from diff and context files. Can be used multiple times.",
        ),
    ] = None,
    context: Annotated[
        list[str] | None,
        typer.Option(
            "--context",
            help="File patterns to include in prompt. Can be used multiple times.",
        ),
    ] = None,
    fetch: Annotated[
        bool | None,
        typer.Option(
            "--fetch/--no-fetch",
            help="Fetch the base ref before generating diffs. Default: False.",
            show_default=False,
        ),
    ] = None,
    version: Annotated[  # noqa: ARG001, FBT002
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Generate a pull request prompt."""
    if write:
        console.print(f"Generating pr {prompt_type.value} prompt...", style="dim")
    overrides = get_overrides(blacklist, context, fetch)
    generator = PrPromptGenerator.from_toml(**overrides)
    generator_method = get_generator_method(generator, prompt_type)
    prompt = generator_method(base_ref)

    if not write:
        print(prompt)  # noqa: T201

    else:
        write_prompt_to_file(prompt_type, prompt)


def get_overrides(
    blacklist: list[str] | None,
    context: list[str] | None,
    fetch: bool | None,  # noqa: FBT001
) -> dict[str, list[str] | bool]:
    overrides: dict[str, list[str] | bool] = {}
    if blacklist is not None:
        overrides["blacklist_patterns"] = blacklist
    if context is not None:
        overrides["context_patterns"] = context
    if fetch is not None:
        overrides["fetch_base"] = fetch
    return overrides


def get_generator_method(
    generator: PrPromptGenerator,
    prompt_type: PromptType,
) -> Callable[[str | None], str]:
    if prompt_type == PromptType.REVIEW:
        return generator.generate_review
    if prompt_type == PromptType.DESCRIPTION:
        return generator.generate_description
    return generator.generate_custom


def write_prompt_to_file(prompt_type: PromptType, prompt: str) -> None:
    output_dir = Path(".pr_prompt")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    output_path = output_dir / f"{prompt_type.value}_{timestamp}.md"
    output_path.write_text(prompt, encoding="utf-8")
    console.print(
        f"✅ Wrote pr {prompt_type.value} prompt to '{output_path}'", style="green"
    )
    console.print(f"File size: {len(prompt):,} characters", style="blue")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
