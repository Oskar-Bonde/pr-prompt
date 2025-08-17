"""Main PR prompt generator."""

from typing import Optional

from .diff_parser import parse_diff_by_files
from .file_filters import FileFilter
from .git_utils import GitClient
from .prompt_builder import PromptBuilder


class PrPromptGenerator:
    """Generator for pull request review prompts."""

    def __init__(self, max_diff_chars: int = 50000):
        self.max_diff_chars = max_diff_chars

    def generate(
        self,
        target_branch: str,
        feature_branch: str,
        custom_instructions: Optional[str] = None,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        blacklist_patterns: Optional[list[str]] = None,
        context_patterns: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a pull request review prompt.

        Args:
            target_branch: Base branch (e.g. `origin/main`).
            feature_branch: Feature branch with changes.
            pr_title: Optional PR title.
            pr_description: Optional PR description.
            blacklist_patterns: File patterns to exclude from diff.
            context_patterns: File patterns to always include in full.
            custom_instructions: Optional custom review instructions.
        """
        blacklist_patterns = blacklist_patterns or []
        git = GitClient()

        git.fetch_branch(target_branch)
        git.fetch_branch(feature_branch)

        builder = PromptBuilder()

        builder.add_instructions(custom_instructions)

        commit_messages = git.get_commit_messages(target_branch, feature_branch)
        builder.add_metadata(
            target_branch,
            feature_branch,
            commit_messages,
            pr_title,
            pr_description,
        )

        if context_patterns:
            all_files = git.list_files(feature_branch)
            context_file_paths = FileFilter.match(all_files, context_patterns)
            context_files = {
                str(file_path): git.get_file_content(feature_branch, file_path)
                for file_path in context_file_paths
            }
            builder.add_context_files(context_files)

        changed_files = git.get_changed_files(target_branch, feature_branch)
        builder.add_changed_files(changed_files)

        file_whitelist = FileFilter.exclude(changed_files, blacklist_patterns)
        diff = git.get_diff(target_branch, feature_branch)
        file_diffs = parse_diff_by_files(diff, file_whitelist)
        builder.add_file_diffs(file_diffs)

        return builder.build()
