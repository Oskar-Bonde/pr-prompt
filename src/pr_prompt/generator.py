"""Generator for pull request prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .instructions import DESCRIPTION_INSTRUCTIONS, REVIEW_INSTRUCTIONS
from .markdown_builder import MarkdownBuilder
from .utils import DiffFile, FileFilter, GitClient, get_diff_files
from .utils.config import load_toml_config
from .utils.errors import MissingCustomInstructionsError


@dataclass
class PrPromptGenerator:
    """
    Generator for pull request prompts.

    This class creates formatted prompts for pull requests using `git diff`.

    Example:
        ```python
        generator = PrPromptGenerator(
            blacklist_patterns=["*.lock", "package-lock.json"],
            include_commit_messages=True,
            default_base_branch="origin/main",
        )
        prompt = generator.generate_review(
            pr_description="Implements OAuth2 with JWT tokens",
        )
        ```

    Attributes:
        blacklist_patterns: File patterns to exclude from diffs and context file inclusion.
            Default: `["*.lock", "package-lock.json"]`.
        context_patterns: File patterns to include in prompt (after blacklist filtering).
            Used for including documentation that provides context.
            Default: `None`.
        fetch_base: Fetch base ref before generating diff.
            Default: `False`.
        diff_context_lines: Number of context lines around changes in diffs.
            Default: `999999`.
        include_commit_messages: Include commit messages in prompt.
            Default: `True`.
        repo_path: The path to either the worktree directory or the .git directory itself.
            Default: Current working directory.
        remote: Git remote name.
            Default: `"origin"`.
        default_base_branch: Used when base_ref not passed. Inferred if omitted.
            Default: Infer from remote (e.g., "origin/main" or "origin/master").
        custom_instructions: Used when `instructions` are not provided in generate_custom.
            Default: `None`.
    """

    blacklist_patterns: list[str] = field(
        default_factory=lambda: ["*.lock", "package-lock.json"]
    )
    context_patterns: Optional[list[str]] = None

    fetch_base: bool = False
    diff_context_lines: int = 999999
    include_commit_messages: bool = True
    repo_path: Optional[str] = None
    remote: str = "origin"
    default_base_branch: Optional[str] = None
    custom_instructions: Optional[str] = None

    @classmethod
    def from_toml(cls, **overrides: list[str] | int | bool | str) -> PrPromptGenerator:
        """
        Create a PrPromptGenerator instance from pyproject.toml configuration.

        Args:
            **overrides: Keyword arguments to override TOML config values.
                Supported keys: blacklist_patterns, context_patterns, fetch_base,
                diff_context_lines, include_commit_messages, repo_path, remote, default_base_branch,
                custom_instructions.

        """
        toml_config = load_toml_config()

        # Merge TOML config with overrides (overrides take precedence)
        config = {**toml_config, **overrides}

        # Filter to only include valid dataclass fields
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_config = {k: v for k, v in config.items() if k in valid_fields}

        return cls(**filtered_config)

    def generate_review(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        *,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Generate a prompt for reviewing a pull request.

        Args:
            base_ref: The base branch/commit to compare against. If None, uses default_base_branch.
            head_ref: The branch/commit with changes. Default: current branch.
            pr_description: The description of the pull request.
        """
        return self._generate(
            REVIEW_INSTRUCTIONS,
            base_ref or self.default_base_branch,
            head_ref,
            pr_description=pr_description,
        )

    def generate_description(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        *,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Generate a prompt for creating PR descriptions.

        Args:
            base_ref: The base branch/commit to compare against. If None, uses default_base_branch.
            head_ref: The branch/commit with changes. Default: current branch.
            pr_description: The description of the pull request.
        """
        return self._generate(
            DESCRIPTION_INSTRUCTIONS,
            base_ref or self.default_base_branch,
            head_ref,
            pr_description=pr_description,
        )

    def generate_custom(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        *,
        instructions: Optional[str] = None,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Generate a pull request prompt with custom instructions.

        Args:
            base_ref: The base branch/commit to compare against. If None, uses default_base_branch.
            head_ref: The branch/commit with changes. Default: current branch.
            instructions: Custom instructions for the LLM. If None, uses custom_instructions.
            pr_description: The description of the pull request.

        """
        final_instructions = instructions or self.custom_instructions
        if final_instructions is None:
            raise MissingCustomInstructionsError

        return self._generate(
            final_instructions,
            base_ref or self.default_base_branch,
            head_ref,
            pr_description=pr_description,
        )

    def generate_overview(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        *,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Generate PR metadata, context files, and changed file tree (no instructions or diffs).

        Args:
            base_ref: The base branch/commit to compare against. If None, uses default_base_branch.
            head_ref: The branch/commit with changes. Default: current branch.
            pr_description: The description of the pull request.
        """
        git = self._create_git_client(base_ref or self.default_base_branch, head_ref)
        diff_files = self._get_filtered_diff_files(git)

        builder = MarkdownBuilder(git)
        builder.add_metadata(
            include_commit_messages=self.include_commit_messages,
            pr_description=pr_description,
        )
        builder.add_context_files(
            self.context_patterns, self.blacklist_patterns, diff_files
        )
        builder.add_changed_files(diff_files)

        return builder.build()

    def generate_diff(
        self,
        file_patterns: list[str],
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> str:
        """
        Generate file diffs for changed files matching the given glob patterns.

        Args:
            file_patterns: Glob patterns to match against changed file paths.
            base_ref: The base branch/commit to compare against. If None, uses default_base_branch.
            head_ref: The branch/commit with changes. Default: current branch.
        """
        git = self._create_git_client(base_ref or self.default_base_branch, head_ref)
        diff_files = self._get_filtered_diff_files(git)

        filtered = {
            path: diff_file
            for path, diff_file in diff_files.items()
            if FileFilter.is_match(path, file_patterns)
        }

        builder = MarkdownBuilder(git)
        builder.add_file_diffs(filtered)

        return builder.build()

    def _create_git_client(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> GitClient:
        """Create a GitClient and optionally fetch the base branch."""
        git = GitClient(
            base_ref, head_ref, repo_path=self.repo_path, remote=self.remote
        )
        if self.fetch_base:
            git.fetch_base_branch()
        return git

    def _get_filtered_diff_files(
        self,
        git: GitClient,
    ) -> dict[str, DiffFile]:
        """Get diff files filtered by blacklist patterns."""
        diff_index = git.get_diff_index(self.diff_context_lines)
        return get_diff_files(diff_index, self.blacklist_patterns)

    def _generate(
        self,
        instructions: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        *,
        pr_description: Optional[str] = None,
    ) -> str:
        """Generate a pull request prompt."""
        git = self._create_git_client(base_ref, head_ref)
        diff_files = self._get_filtered_diff_files(git)

        builder = MarkdownBuilder(git)

        builder.add_instructions(instructions)

        builder.add_metadata(
            include_commit_messages=self.include_commit_messages,
            pr_description=pr_description,
        )

        builder.add_context_files(
            self.context_patterns, self.blacklist_patterns, diff_files
        )

        builder.add_changed_files(diff_files)

        builder.add_file_diffs(diff_files)

        return builder.build()
