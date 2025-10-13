from dataclasses import dataclass
from typing import Optional

from .utils import (
    DiffFile,
    FileFilter,
    GitClient,
    build_file_tree,
    get_markdown_content,
)


@dataclass
class MarkdownSection:
    title: str
    content: str = ""
    heading_level: int = 2

    def render(self) -> str:
        """Render the section as markdown."""
        heading = "#" * self.heading_level
        if self.content:
            return f"{heading} {self.title}\n\n{self.content}"
        return f"{heading} {self.title}"


class MarkdownBuilder:
    """Builds structured markdown prompts for pull request."""

    def __init__(self, git_client: GitClient) -> None:
        self.git_client = git_client
        self.sections: list[MarkdownSection] = []

    def add_instructions(self, instructions: str) -> None:
        self.sections.append(
            MarkdownSection(title="Instructions", content=instructions.strip())
        )

    def add_metadata(
        self,
        *,
        include_commit_messages: bool,
        pr_description: Optional[str],
    ) -> None:
        """Add PR metadata section."""
        content_parts = []

        content_parts.append(f"**Repository:** {self.git_client.get_repo_name()}")

        content_parts.append(
            f"**Branch:** `{self.git_client.head_ref}` -> `{self.git_client.base_ref}`"
        )

        if pr_description:
            content_parts.append(f"**Description:**\n\n{pr_description}")

        if include_commit_messages:
            commit_messages = self.git_client.get_commit_messages()
            commits_text = "\n".join(f"- {msg}" for msg in commit_messages)
            content_parts.append(f"**Commits:**\n{commits_text}")

        self.sections.append(
            MarkdownSection(
                title="Pull Request Details",
                content="\n\n".join(content_parts),
            )
        )

    def add_context_files(
        self, context_patterns: list[str], blacklist_patterns: list[str]
    ) -> None:
        """Add a context files section with a main heading and sub-headings for each file, excluding blacklisted files."""
        if not context_patterns:
            return

        all_files = self.git_client.list_files(self.git_client.head_ref)
        all_context_files = FileFilter.include(all_files, context_patterns)

        context_files = FileFilter.exclude(all_context_files, blacklist_patterns)

        if not context_files:
            return

        self.sections.append(MarkdownSection(title="Context Files"))
        for file_path in context_files:
            content = self.git_client.get_file_content(
                self.git_client.head_ref, file_path
            )
            content_md = get_markdown_content(file_path, content)
            self.sections.append(
                MarkdownSection(
                    title=f"File: `{file_path}`",
                    content=content_md,
                    heading_level=3,
                )
            )

    def add_changed_files_tree(self, diff_files: dict[str, DiffFile]) -> None:
        """Add changed files in a tree format."""
        file_tree = build_file_tree(diff_files)

        self.sections.append(
            MarkdownSection(
                title="Changed Files",
                content=f"```\n{file_tree}\n```",
            )
        )

    def add_file_diffs(self, file_diffs: dict[str, DiffFile]) -> None:
        """Add file diffs with individual headings for each file."""
        self.sections.append(MarkdownSection(title="File diffs"))

        for file_path, diff_file in file_diffs.items():
            self.sections.append(
                MarkdownSection(
                    title=f"{diff_file.change_type} `{file_path}`",
                    content=diff_file.content,
                    heading_level=3,
                )
            )

    def build(self) -> str:
        """Build the final prompt."""
        if not self.sections:
            return ""

        prompt_parts = [section.render() for section in self.sections]

        return "\n\n".join(prompt_parts)
