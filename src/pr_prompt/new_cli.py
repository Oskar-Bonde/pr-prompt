"""Command-line interface for pr-prompt."""

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from . import __version__
from .generator import PrPromptGenerator
from .utils.config import load_config

app = typer.Typer(
    help="Generate structured prompts for LLM-powered pull request reviews.",
    rich_markup_mode="rich",
)
console = Console()


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"✅ {message}", style="green")


def error(message: str) -> None:
    """Print an error message."""
    console.print(f"❌ {message}", style="red", file=sys.stderr)


def info(message: str) -> None:
    """Print an info message."""
    console.print(f"i  {message}", style="blue")


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"pr-prompt version {__version__}")
        raise typer.Exit()


def generate_and_output(
    generator: PrPromptGenerator,
    command_type: str,
    output: Optional[Path],
    stdout: bool,  # noqa: FBT001
    base_ref: str,
    head_ref: Optional[str],
    **kwargs,
) -> None:
    """Generate prompt and handle output."""
    info(
        f"Generating {command_type} prompt (base: {base_ref}, head: {head_ref or 'current branch'})..."
    )

    # Generate prompt based on command type
    if command_type == "review":
        prompt = generator.generate_review(
            base_ref=base_ref,
            head_ref=head_ref,
        )
        default_filename = "review_prompt.md"
    elif command_type == "description":
        prompt = generator.generate_description(
            base_ref=base_ref,
            head_ref=head_ref,
        )
        default_filename = "description_prompt.md"
    elif command_type == "custom":
        prompt = generator.generate_custom(
            instructions=kwargs["instructions"],
            base_ref=base_ref,
            head_ref=head_ref,
        )
        default_filename = "custom_prompt.md"
    else:
        msg = f"Unknown command type: {command_type}"
        raise ValueError(msg)

    # Handle output
    if stdout:
        console.print(prompt)
    else:
        output_path = output or Path(default_filename)
        output_path.write_text(prompt, encoding="utf-8")
        success(f"Wrote {command_type} prompt to {output_path}")
        info(f"File size: {len(prompt):,} characters")


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            help="Show the version and exit.",
        ),
    ] = None,
) -> None:
    """
    Generate structured prompts for LLM-powered pull request reviews.

    pr-prompt analyzes git diffs, commit messages, and file changes to create
    comprehensive prompts that help Large Language Models provide better code
    reviews and generate meaningful pull request descriptions.
    """


@app.command()
def review(
    base_ref: Annotated[
        str,
        typer.Option(
            "--base-ref",
            "-b",
            help="Base branch/commit to compare against (e.g., origin/main)",
        ),
    ],
    head_ref: Annotated[
        Optional[str],
        typer.Option(
            "--head-ref",
            "-h",
            help="Head branch/commit with changes (default: current branch)",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: auto-generated based on command)",
        ),
    ] = None,
    stdout: Annotated[
        bool, typer.Option("--stdout", help="Output to stdout instead of file")
    ] = False,
    blacklist: Annotated[
        list[str],
        typer.Option(
            "--blacklist",
            help="Additional file patterns to exclude (can be used multiple times)",
        ),
    ] = [],
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            help="Additional context file patterns (can be used multiple times)",
        ),
    ] = [],
    no_commits: Annotated[
        bool,
        typer.Option("--no-commits", help="Exclude commit messages from the prompt"),
    ] = False,
    diff_context: Annotated[
        Optional[int],
        typer.Option(
            "--diff-context",
            help="Number of context lines around changes (default: full file)",
        ),
    ] = None,
) -> None:
    """
    Generate a code review prompt for a pull request.

    Creates a structured prompt optimized for LLM code review, including
    instructions to identify bugs, security issues, and suggest improvements.

    Examples:
        # Basic usage - review changes against main branch
        pr-prompt review --base-ref origin/main

        # Exclude test files and include specific docs
        pr-prompt review -b origin/main --blacklist "*test*.py" --context "docs/*.md"
    """
    try:
        config = load_config()

        # Merge CLI options with config
        blacklist_patterns = list(config.blacklist_patterns) + blacklist
        context_patterns = list(config.context_patterns) + context

        generator = PrPromptGenerator(
            blacklist_patterns=blacklist_patterns,
            context_patterns=context_patterns,
            include_commit_messages=not no_commits,
            diff_context_lines=diff_context or 999999,
        )

        generate_and_output(
            generator=generator,
            command_type="review",
            output=output,
            stdout=stdout,
            base_ref=base_ref,
            head_ref=head_ref,
        )

    except Exception as e:
        error(f"Failed to generate review prompt: {e}")
        raise typer.Exit(1)


@app.command()
def description(
    base_ref: Annotated[
        str,
        typer.Option(
            "--base-ref",
            "-b",
            help="Base branch/commit to compare against (e.g., origin/main)",
        ),
    ],
    head_ref: Annotated[
        Optional[str],
        typer.Option(
            "--head-ref",
            "-h",
            help="Head branch/commit with changes (default: current branch)",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: auto-generated based on command)",
        ),
    ] = None,
    stdout: Annotated[
        bool, typer.Option("--stdout", help="Output to stdout instead of file")
    ] = False,
    blacklist: Annotated[
        list[str],
        typer.Option(
            "--blacklist",
            help="Additional file patterns to exclude (can be used multiple times)",
        ),
    ] = [],
    context: Annotated[
        list[str],
        typer.Option(
            "--context",
            help="Additional context file patterns (can be used multiple times)",
        ),
    ] = [],
    no_commits: Annotated[
        bool,
        typer.Option("--no-commits", help="Exclude commit messages from the prompt"),
    ] = False,
) -> None:
    """
    Generate a prompt for creating PR descriptions.

    Creates a structured prompt that helps LLMs write comprehensive pull request
    descriptions, including change summaries, context, and impact documentation.

    Examples:
        # Basic usage
        pr-prompt description --base-ref origin/main

        # Output to stdout for piping
        pr-prompt description -b origin/main --stdout | pbcopy
    """
    try:
        config = load_config()

        # Merge CLI options with config
        blacklist_patterns = list(config.blacklist_patterns) + blacklist
        context_patterns = list(config.context_patterns) + context

        generator = PrPromptGenerator(
            blacklist_patterns=blacklist_patterns,
            context_patterns=context_patterns,
            include_commit_messages=not no_commits,
        )

        generate_and_output(
            generator=generator,
            command_type="description",
            output=output,
            stdout=stdout,
            base_ref=base_ref,
            head_ref=head_ref,
        )

    except Exception as e:
        error(f"Failed to generate description prompt: {e}")
        raise typer.Exit(1)


@app.command()
def custom(
    instructions: Annotated[
        str,
        typer.Option("--instructions", "-i", help="Custom instructions for the LLM"),
    ],
    base_ref: Annotated[
        str,
        typer.Option(
            "--base-ref",
            "-b",
            help="Base branch/commit to compare against (e.g., origin/main)",
        ),
    ],
    head_ref: Annotated[
        Optional[str],
        typer.Option(
            "--head-ref",
            "-h",
            help="Head branch/commit with changes (default: current branch)",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: auto-generated based on command)",
        ),
    ] = None,
    stdout: Annotated[
        bool, typer.Option("--stdout", help="Output to stdout instead of file")
    ] = False,
) -> None:
    """
    Generate a custom prompt with specific instructions.

    Allows you to create prompts with your own instructions for specialized
    use cases like security audits, performance reviews, or documentation checks.

    Examples:
        # Security-focused review
        pr-prompt custom -i "Focus on security vulnerabilities and data leaks" -b origin/main

        # Documentation review
        pr-prompt custom -i "Check if all new functions have proper docstrings" -b main
    """
    try:
        config = load_config()
        generator = PrPromptGenerator(
            blacklist_patterns=config.blacklist_patterns,
            context_patterns=config.context_patterns,
        )

        generate_and_output(
            generator=generator,
            command_type="custom",
            output=output,
            stdout=stdout,
            base_ref=base_ref,
            head_ref=head_ref,
            instructions=instructions,
        )

    except Exception as e:
        error(f"Failed to generate custom prompt: {e}")
        raise typer.Exit(1)


@app.command()
def init() -> None:
    """
    Initialize pr-prompt configuration in the current project.

    Creates a pyproject.toml with default pr-prompt settings if it doesn't exist,
    or adds pr-prompt configuration to an existing pyproject.toml file.
    """
    try:
        import tomli
        import tomli_w
    except ImportError:
        error("Please install tomli-w to use this command: pip install tomli-w")
        raise typer.Exit(1)

    pyproject_path = Path("pyproject.toml")

    # Load existing or create new config
    if pyproject_path.exists():
        with pyproject_path.open("rb") as f:
            data = tomli.load(f)
        info("Found existing pyproject.toml")
    else:
        data = {}
        info("Creating new pyproject.toml")

    # Add pr-prompt config if not present
    if "tool" not in data:
        data["tool"] = {}

    if "pr-prompt" in data["tool"]:
        info("pr-prompt configuration already exists in pyproject.toml")
        return

    # Add default configuration
    data["tool"]["pr-prompt"] = {
        "blacklist_patterns": [
            "*.lock",
            "*.min.js",
            "*.min.css",
            "dist/*",
            "build/*",
            "*.generated.*",
        ],
        "context_patterns": [
            "*.md",
        ],
    }

    # Write back
    with pyproject_path.open("wb") as f:
        tomli_w.dump(data, f)

    success("Initialized pr-prompt configuration in pyproject.toml")
    info("You can now customize the settings in [tool.pr-prompt] section")


def main_entry_point() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()
