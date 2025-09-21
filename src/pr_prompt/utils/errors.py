"""Custom exceptions for pr-prompt."""

from __future__ import annotations


class PrPromptError(Exception):
    """Base exception for pr-prompt."""


class MissingCustomInstructionsError(PrPromptError):
    """Raised when custom instructions are required but not provided."""

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = (
                "No instructions provided to PrPromptGenerator. You can provide instructions in one of these ways:\n"
                " - Pass 'custom_instructions' parameter to PrPromptGenerator() constructor\n"
                " - Set 'custom_instructions' in [tool.pr-prompt] section of pr_prompt.toml or pyproject.toml\n"
                " - Pass 'instructions' parameter to PrPromptGenerator.generate_custom()"
            )
        super().__init__(message)


class InvalidConfigError(PrPromptError):
    """Raised when configuration is invalid."""
