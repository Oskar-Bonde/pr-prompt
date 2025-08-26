from pathlib import Path

import click

from .generator import PrPromptGenerator
from .utils.config import load_config


@click.group()
def main() -> None:
    """Generate pull request prompts using git diffs."""


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="review.md",
    help="Output file path (default: review.md)",
)
@click.option(
    "--target-branch", "-t", help="Target branch to compare against", required=True
)
def review(output: str, target_branch: str) -> None:
    """Write a pull request review prompt to <output>."""
    click.echo(f"Comparing to {target_branch}...")

    config = load_config()
    generator = PrPromptGenerator(
        blacklist_patterns=config.blacklist_patterns,
        context_patterns=config.context_patterns,
    )
    prompt = generator.generate_review(target_branch)

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
    "--target-branch", "-t", help="Target branch to compare against", required=True
)
def description(output: str, target_branch: str) -> None:
    """Write a pull request description prompt to <output>."""
    click.echo(f"Comparing to {target_branch}...")

    config = load_config()
    generator = PrPromptGenerator(
        blacklist_patterns=config.blacklist_patterns,
        context_patterns=config.context_patterns,
    )
    prompt = generator.generate_description(target_branch)

    output_path = Path(output)
    output_path.write_text(prompt, encoding="utf-8")

    click.echo(f"✅ Wrote pr description prompt to {output_path}")


if __name__ == "__main__":
    main()
