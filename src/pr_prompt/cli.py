from pathlib import Path
from typing import Callable

import typer

from .generator import PrPromptGenerator
from .utils.config import load_config

app = typer.Typer(help="Generate pull request prompts using git diff.")


def _generate_prompt(
    base_ref: str,
    output: str,
    generator_method: Callable[[str], str],
    prompt_type: str,
) -> None:
    """Common logic for generating prompts."""
    typer.echo(f"Comparing to {base_ref}...")

    config = load_config()
    generator = PrPromptGenerator(
        blacklist_patterns=config.blacklist_patterns,
        context_patterns=config.context_patterns,
    )
    prompt = generator_method(base_ref)

    output_path = Path(output)
    output_path.write_text(prompt, encoding="utf-8")

    typer.echo(f"✅ Wrote pr {prompt_type} prompt to {output_path}")


@app.command()
def review(
    output: str = typer.Option(
        "review.md",
        "--output",
        "-o",
        help="Output file path (default: review.md)",
    ),
    base_ref: str = typer.Option(
        ...,
        "--base-ref",
        "-b",
        help="The branch/commit to compare against",
    ),
) -> None:
    """Write a pull request review prompt to <output>."""
    config = load_config()
    generator = PrPromptGenerator(
        blacklist_patterns=config.blacklist_patterns,
        context_patterns=config.context_patterns,
    )
    _generate_prompt(base_ref, output, generator.generate_review, "review")


@app.command()
def description(
    output: str = typer.Option(
        "description.md",
        "--output",
        "-o",
        help="Output file path (default: description.md)",
    ),
    base_ref: str = typer.Option(
        ...,
        "--base-ref",
        "-b",
        help="The branch/commit to compare against",
    ),
) -> None:
    """Write a pull request description prompt to <output>."""
    config = load_config()
    generator = PrPromptGenerator(
        blacklist_patterns=config.blacklist_patterns,
        context_patterns=config.context_patterns,
    )
    _generate_prompt(base_ref, output, generator.generate_description, "description")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
