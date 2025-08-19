from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .diff_parser import DiffFile
from .file_tree import build_file_tree
from .git_utils import GitClient


@dataclass
class PromptSection:
    """Represents a section of the prompt."""

    title: str
    content: str = ""
    heading_level: int = 2

    def render(self) -> str:
        """Render the section as markdown."""
        heading = "#" * self.heading_level
        if self.content:
            return f"{heading} {self.title}\n\n{self.content}"
        return f"{heading} {self.title}"


class PromptBuilder:
    """Builds structured prompts for pull request review."""

    def __init__(self) -> None:
        self.sections: list[PromptSection] = []

    def add_instructions(self, instructions: str) -> None:
        self.sections.append(PromptSection(title="Instructions", content=instructions))

    def add_metadata(
        self,
        target_branch: str,
        feature_branch: str,
        *,
        include_commit_messages: bool,
        pr_title: Optional[str],
        pr_description: Optional[str],
    ) -> None:
        """Add PR metadata section."""
        content_parts = []

        repo_name = GitClient.get_repo_name()

        content_parts.append(f"**Repository:** {repo_name}")

        content_parts.append(f"**Branch:** `{feature_branch}` -> `{target_branch}`")

        if pr_title:
            content_parts.append(f"**Title:** {pr_title}")

        if pr_description:
            content_parts.append(f"**Description:**\n\n{pr_description}")

        if include_commit_messages:
            commit_messages = GitClient.get_commit_messages(
                target_branch, feature_branch
            )
            commits_text = "\n".join(f" - {msg}" for msg in commit_messages)
            content_parts.append(f"**Commits:**\n{commits_text}")

        if content_parts:
            self.sections.append(
                PromptSection(
                    title="Pull Request Details",
                    content="\n\n".join(content_parts),
                )
            )

    def add_changed_files(self, files: list[str]) -> None:
        file_tree = build_file_tree(files) if files else "No files changed"

        self.sections.append(
            PromptSection(
                title="Changed Files",
                content=f"```\n{file_tree}\n```",
            )
        )

    def add_file_diffs(self, file_diffs: dict[str, DiffFile]) -> None:
        """Add file diffs with individual headings for each file."""
        self.sections.append(PromptSection(title="File diffs"))

        for file_path, diff_file in file_diffs.items():
            content = f"```diff\n{diff_file.content}\n```"

            self.sections.append(
                PromptSection(
                    title=f"{diff_file.operation_type.value} `{file_path}`",
                    content=content,
                    heading_level=3,
                )
            )

    def add_context_files(self, context_files: dict[str, str]) -> None:
        """Add a context files section with a main heading and sub-headings for each file."""
        self.sections.append(PromptSection(title="Context Files"))
        for file_path, content in context_files.items():
            content_md = self.get_markdown_content(file_path, content)
            self.sections.append(
                PromptSection(
                    title=f"File: `{file_path}`",
                    content=content_md,
                    heading_level=3,
                )
            )

    def get_markdown_content(self, file_path: str, content: str) -> str:
        extension = Path(file_path).suffix[1:]
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "jsx",
            "tsx": "tsx",
            "java": "java",
            "go": "go",
            "rs": "rust",
            "cpp": "cpp",
            "c": "c",
            "cs": "csharp",
            "rb": "ruby",
            "php": "php",
            "swift": "swift",
            "kt": "kotlin",
            "scala": "scala",
            "sh": "bash",
            "yml": "yaml",
            "yaml": "yaml",
            "json": "json",
            "xml": "xml",
            "html": "html",
            "css": "css",
            "sql": "sql",
            "md": "markdown",
        }
        lang = lang_map.get(extension, "text")

        if lang == "markdown":
            content = f"~~~{lang}\n{content}\n~~~"
        else:
            content = f"```{lang}\n{content}\n```"
        return content

    def build(self) -> str:
        """Build the final prompt."""
        if not self.sections:
            return ""

        prompt_parts = [section.render() for section in self.sections]

        return "\n\n".join(prompt_parts)
