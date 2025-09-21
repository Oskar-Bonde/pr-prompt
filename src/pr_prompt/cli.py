from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown

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
    review = "review"
    description = "description"
    custom = "custom"


@app.command()
def generate(
    prompt_type: Annotated[
        PromptType,
        typer.Argument(
            help="Type of prompt to generate",
            case_sensitive=False,
        ),
    ] = PromptType.review,
    base_ref: Annotated[
        str | None,
        typer.Option(
            "--base-ref",
            "-b",
            help="The branch/commit to compare against. Infer from default branch if not provided",
        ),
    ] = None,
    stdout: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--stdout",
            help="Output to stdout instead of writing to file",
        ),
    ] = False,
    blacklist: Annotated[
        list[str] | None,
        typer.Option(
            "--blacklist",
            help="File patterns to exclude from diff analysis (can be used multiple times)",
        ),
    ] = None,
    context: Annotated[
        list[str] | None,
        typer.Option(
            "--context",
            help="File patterns to include as context (can be used multiple times)",
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
    if not stdout:
        console.print(f"Generating pr {prompt_type.value} prompt...", style="dim")
    overrides = get_overrides(blacklist, context)
    generator = PrPromptGenerator.from_toml(**overrides)
    generator_method = get_generator_method(generator, prompt_type)
    prompt = generator_method(base_ref)

    if stdout:
        console.print(Markdown(prompt))
    else:
        output_path = Path(f"{prompt_type.value}.md")
        output_path.write_text(prompt, encoding="utf-8")
        console.print(
            f"✅ Wrote pr {prompt_type.value} prompt to {output_path}", style="green"
        )
        console.print(f"File size: {len(prompt):,} characters", style="blue")


def get_overrides(
    blacklist: list[str] | None, context: list[str] | None
) -> dict[str, list[str]]:
    overrides = {}
    if blacklist is not None:
        overrides["blacklist_patterns"] = blacklist
    if context is not None:
        overrides["context_patterns"] = context
    return overrides


def get_generator_method(
    generator: PrPromptGenerator,
    prompt_type: PromptType,
) -> callable:
    if prompt_type == PromptType.review:
        return generator.generate_review
    if prompt_type == PromptType.description:
        return generator.generate_description
    return generator.generate_custom


def main() -> None:
    app()


if __name__ == "__main__":
    main()
