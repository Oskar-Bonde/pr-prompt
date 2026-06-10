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
    *,
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
    write: Annotated[
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
    version: Annotated[  # noqa: ARG001
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Generate a full pull request prompt (instructions + metadata + context + tree + diffs)."""
    if write:
        console.print(f"Generating pr {prompt_type.value} prompt...", style="dim")
    overrides = _get_overrides(blacklist=blacklist, context=context, fetch=fetch)
    generator = PrPromptGenerator.from_toml(**overrides)
    generator_method = _get_generator_method(generator, prompt_type)
    prompt = generator_method(base_ref)

    _output(prompt, write=write, label=prompt_type.value)


@app.command()
def overview(
    *,
    base_ref: Annotated[
        str | None,
        typer.Option(
            "--base-ref",
            "-b",
            help="The branch/commit to compare against (e.g., 'origin/main'). Infer from default branch if not provided.",
        ),
    ] = None,
    write: Annotated[
        bool,
        typer.Option(
            "--write",
            help="Write to .pr_prompt/overview_<timestamp>.md instead of stdout.",
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
) -> None:
    """Generate PR metadata, context files, and changed file tree (no instructions or diffs)."""
    overrides = _get_overrides(blacklist=blacklist, context=context, fetch=fetch)
    generator = PrPromptGenerator.from_toml(**overrides)
    prompt = generator.generate_overview(base_ref)

    _output(prompt, write=write, label="overview")


@app.command()
def diff(
    *,
    file_patterns: Annotated[
        list[str],
        typer.Argument(
            help="Glob patterns to match against changed file paths (e.g., 'src/*.py' '*.md').",
        ),
    ],
    context_lines: Annotated[
        int | None,
        typer.Option(
            "--context-lines",
            help="Number of context lines around changes in diffs. Default: 999999 (full file).",
        ),
    ] = None,
    base_ref: Annotated[
        str | None,
        typer.Option(
            "--base-ref",
            "-b",
            help="The branch/commit to compare against (e.g., 'origin/main'). Infer from default branch if not provided.",
        ),
    ] = None,
    write: Annotated[
        bool,
        typer.Option(
            "--write",
            help="Write to .pr_prompt/diff_<timestamp>.md instead of stdout.",
        ),
    ] = False,
    blacklist: Annotated[
        list[str] | None,
        typer.Option(
            "--blacklist",
            help="File patterns to exclude from diff. Can be used multiple times.",
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
) -> None:
    """Generate file diffs for changed files matching the given glob patterns."""
    overrides = _get_overrides(
        blacklist=blacklist, context=None, fetch=fetch, diff_context_lines=context_lines
    )
    generator = PrPromptGenerator.from_toml(**overrides)
    prompt = generator.generate_diff(file_patterns, base_ref)

    if prompt is None:
        typer.echo(f"No changed files matched: {', '.join(file_patterns)}", err=True)
        return

    _output(prompt, write=write, label="diff")


def _get_overrides(
    *,
    blacklist: list[str] | None,
    context: list[str] | None,
    fetch: bool | None,
    diff_context_lines: int | None = None,
) -> dict[str, list[str] | bool | int]:
    overrides: dict[str, list[str] | bool | int] = {}
    if blacklist is not None:
        overrides["blacklist_patterns"] = blacklist
    if context is not None:
        overrides["context_patterns"] = context
    if fetch is not None:
        overrides["fetch_base"] = fetch
    if diff_context_lines is not None:
        overrides["diff_context_lines"] = diff_context_lines
    return overrides


def _get_generator_method(
    generator: PrPromptGenerator,
    prompt_type: PromptType,
) -> Callable[[str | None], str]:
    if prompt_type == PromptType.REVIEW:
        return generator.generate_review
    if prompt_type == PromptType.DESCRIPTION:
        return generator.generate_description
    return generator.generate_custom


def _output(prompt: str, *, write: bool, label: str) -> None:
    if not write:
        print(prompt)  # noqa: T201
    else:
        _write_prompt_to_file(label, prompt)


def _write_prompt_to_file(label: str, prompt: str) -> None:
    output_dir = Path(".pr_prompt")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    output_path = output_dir / f"{label}_{timestamp}.md"
    output_path.write_text(prompt, encoding="utf-8")
    console.print(f"✅ Wrote pr {label} prompt to '{output_path}'", style="green")
    console.print(f"File size: {len(prompt):,} characters", style="blue")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
