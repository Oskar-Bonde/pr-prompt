"""Generator for pull request review prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .diff_parser import clean_file_diffs, parse_diff_by_files
from .file_filters import FileFilter
from .git_utils import GitClient
from .prompt_builder import PromptBuilder


@dataclass
class PrPromptGenerator:
    """
    Generator for pull request review prompts.

    This class creates formatted prompts for LLM review of pull requests by analyzing
    git diffs, commit messages, and file changes between branches.

    Example:
        ```python
        generator = PrPromptGenerator(
            blacklist_patterns=["*.lock", "*.log", "dist/*"],
            context_patterns=[".github/copilot-instructions.md"],
            include_commit_messages=True,
        )
        prompt = generator.generate(
            target_branch="origin/main",
            feature_branch="feature/auth-system",
            pr_title="Add new authentication system",
            pr_description="Implements OAuth2 with JWT tokens",
        )
        ```

    Attributes:
        instructions: Overwrite prompt instructions.
        blacklist_patterns: File patterns to exclude from the diff analysis.
            Files with space are always excluded `"* *"`.
            Default: `["*.lock", "*.log"]`.
        context_patterns: File patterns to include in full content (not just diffs).
            Useful for including documentation that provide context for the review.
        diff_context_lines: Number of context lines around changes in diffs.
            Default: `999999` to include full file context.
        include_commit_messages: Whether to include commit messages in the prompt.
            Default: `True`.
    """

    # Content settings
    instructions: Optional[
        str
    ] = """You are an expert software engineer reviewing a pull request.

Your task:
 - Identify Issues: Find potential bugs, security vulnerabilities, and performance problems
 - Suggest Improvements: Recommend refactorings and best practices
 - Assess Clarity: Point out unclear or overly complex code
 - Be Specific: Reference line numbers and provide concrete examples

Focus on actionable feedback that improves code quality and maintainability."""

    # File filtering
    blacklist_patterns: list[str] = field(default_factory=lambda: ["*.lock", "*.log"])
    context_patterns: list[str] = field(default_factory=list)

    # Advanced options
    diff_context_lines: int = 999999
    include_commit_messages: bool = True

    def generate(
        self,
        target_branch: str,
        feature_branch: Optional[str] = None,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Generate a pull request review prompt.

        Args:
            target_branch: Base branch (e.g. `origin/main`, `origin/master`).
            feature_branch: Feature branch with changes. Auto-detects if None.
            pr_title: Optional pull request title.
            pr_description: Optional pull request description.

        Returns:
            A formatted prompt for LLM pull request review.
        """
        git = GitClient()

        if not feature_branch:
            feature_branch = git.get_current_branch()
        git.fetch_branch(target_branch)
        git.fetch_branch(feature_branch)

        builder = PromptBuilder()

        builder.add_instructions(self.instructions)

        if self.include_commit_messages:
            commit_messages = git.get_commit_messages(target_branch, feature_branch)
        else:
            commit_messages = []

        builder.add_metadata(
            target_branch,
            feature_branch,
            commit_messages=commit_messages,
            pr_title=pr_title,
            pr_description=pr_description,
        )

        if self.context_patterns:
            all_files = git.list_files(feature_branch)
            context_file_paths = FileFilter.match(all_files, self.context_patterns)
            context_files = {
                file_path: git.get_file_content(feature_branch, file_path)
                for file_path in context_file_paths
            }
            builder.add_context_files(context_files)

        changed_files = git.get_changed_files(target_branch, feature_branch)
        builder.add_changed_files(changed_files)

        blacklist_patterns = self.blacklist_patterns.copy()
        # Always exclude files with whitespace in their names
        blacklist_patterns.append("* *")

        file_whitelist = FileFilter.exclude(changed_files, blacklist_patterns)
        diff = git.get_diff(target_branch, feature_branch, self.diff_context_lines)
        file_diffs = parse_diff_by_files(diff, file_whitelist)
        cleaned_diffs = clean_file_diffs(file_diffs)
        builder.add_file_diffs(cleaned_diffs)

        return builder.build()
