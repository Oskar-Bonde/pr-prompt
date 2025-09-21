from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from .generator import PrPromptGenerator

app = typer.Typer(help="Generate pull request prompts using git diff.")


class PromptType(str, Enum):
    review = "review"
    description = "description"
    custom = "custom"


@app.command()
def generate(
    prompt_type: Annotated[
        PromptType,
        typer.Argument(
            PromptType.review,
            help="Type of prompt to generate",
            case_sensitive=False,
        ),
    ],
    stdout: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--stdout",
            help="Output to stdout instead of writing to file",
        ),
    ] = False,
    base_ref: Annotated[
        str | None,
        typer.Option(
            "--base-ref",
            "-b",
            help="The branch/commit to compare against. Infer from default branch if not provided",
        ),
    ] = None,
) -> None:
    """Generate a pull request prompt."""
    generator = PrPromptGenerator().from_toml()

    if prompt_type == PromptType.review:
        generator_method = generator.generate_review
    elif prompt_type == PromptType.description:
        generator_method = generator.generate_description
    else:
        generator_method = generator.generate_custom

    typer.echo("Comparing to base ref...")

    prompt = generator_method(base_ref)

    if stdout:
        typer.echo(prompt)
    else:
        output_path = Path(f"{prompt_type.value}.md")
        output_path.write_text(prompt, encoding="utf-8")
        typer.echo(f"✅ Wrote pr {prompt_type.value} prompt to {output_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
