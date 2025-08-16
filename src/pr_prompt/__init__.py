"""PR Prompt - Generate pull request review prompts for LLMs."""

from .entrypoint import get_pr_prompt

__version__ = "0.1.0"
__all__ = ["get_pr_prompt"]
