from pathlib import Path

import click

from .generator import PrPromptGenerator


@click.group()
def main() -> None:
    """Generate pull request prompts using git diff."""


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="review.md",
    help="Output file path (default: review.md)",
)
@click.option(
    "--base-ref", "-b", help="The branch/commit to compare against", required=True
)
def review(output: str, base_ref: str) -> None:
    """Write a pull request review prompt to <output>."""
    click.echo(f"Comparing to {base_ref}...")

    generator = PrPromptGenerator.from_toml()
    prompt = generator.generate_review(base_ref)

    output_path = Path(output)
    output_path.write_text(prompt, encoding="utf-8")

    click.echo(f"✅ Wrote pr review prompt to {output_path}")


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="description.md",
    help="Output file path (default: description.md)",
)
@click.option(
    "--base-ref", "-b", help="The branch/commit to compare against", required=True
)
def description(output: str, base_ref: str) -> None:
    """Write a pull request description prompt to <output>."""
    click.echo(f"Comparing to {base_ref}...")

    generator = PrPromptGenerator.from_toml()
    prompt = generator.generate_description(base_ref)

    output_path = Path(output)
    output_path.write_text(prompt, encoding="utf-8")

    click.echo(f"✅ Wrote pr description prompt to {output_path}")


if __name__ == "__main__":
    main()
