"""Main entrypoint."""

from typing import Optional

from .generator import PrPromptGenerator


def get_pr_prompt(
    target_branch: str,
    feature_branch: str,
    pr_title: Optional[str] = None,
    pr_description: Optional[str] = None,
    max_diff_chars: int = 15000,
    blacklist_files: Optional[list[str]] = None,
    context_files: Optional[list[str]] = None,
) -> str:
    """
    Generate a pull request review prompt.

    Args:
        target_branch: Branch to compare against (e.g., 'origin/main').
        feature_branch: Branch containing the changes.
        pr_title: Optional pull request title.
        pr_description: Optional pull request description.
        max_diff_chars: Maximum characters to include from diff.
        blacklist_files: File patterns to exclude from diff.
        context_files: File patterns to include in full.

    Returns:
        A formatted prompt for LLM pull request review.

    Example:
        >>> prompt = get_pr_prompt(
        ...     target_branch="origin/main",
        ...     feature_branch="feature/new-feature",
        ...     pr_title="Add new authentication system",
        ...     blacklist_files=["*.lock"],
        ...     context_files=["README.md"],
        ... )
    """
    generator = PrPromptGenerator(
        max_diff_chars=max_diff_chars    )

    return generator.generate(
        target_branch=target_branch,
        feature_branch=feature_branch,
        pr_title=pr_title,
        pr_description=pr_description,
        blacklist_patterns=blacklist_files,
        context_patterns=context_files,
    )
