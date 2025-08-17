"""Prompt building utilities."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PromptSection:
    """Represents a section of the prompt."""

    title: str
    content: str
    level: int = 2  # Markdown heading level

    def render(self) -> str:
        """Render the section as markdown."""
        heading = "#" * self.level
        return f"{heading} {self.title}\n\n{self.content}"


class PromptBuilder:
    """Builds structured prompts for pull request review."""

    DEFAULT_INSTRUCTIONS = """You are an expert software engineer reviewing a pull request.

Your task:
 - Identify Issues: Find potential bugs, security vulnerabilities, and performance problems
 - Suggest Improvements: Recommend refactorings and best practices
 - Assess Clarity: Point out unclear or overly complex code
 - Be Specific: Reference line numbers and provide concrete examples

Focus on actionable feedback that improves code quality and maintainability."""

    def __init__(self) -> None:
        """
        Initialize the prompt builder.

        Args:
            instructions: Optional custom review instructions.
        """
        self.sections: list[PromptSection] = []

    def add_instructions(self, instructions: Optional[str] = None) -> None:
        instructions = instructions or self.DEFAULT_INSTRUCTIONS
        """Add the review instructions section."""
        self.sections.append(
            PromptSection(
                title="Pull Request Review Instructions", content=instructions, level=2
            )
        )

    def add_metadata(
        self, pr_title: Optional[str] = None, pr_description: Optional[str] = None
    ) -> None:
        """Add PR metadata section."""
        content_parts = []

        if pr_title:
            content_parts.append(f"**Title:** {pr_title}")

        if pr_description:
            content_parts.append(f"**Description:**\n\n{pr_description}")

        if content_parts:
            self.sections.append(
                PromptSection(
                    title="Pull Request Details",
                    content="\n\n".join(content_parts),
                    level=2,
                )
            )

    def add_changed_files(self, files: list[Path]) -> None:
        if files:
            # Group files by directory for better organization
            files_by_dir: dict[str, list[Path]] = defaultdict(list)
            for file in sorted(files):
                dir_path = file.parent if file.parent != Path() else Path()
                files_by_dir[str(dir_path)].append(file)

            content_parts = []
            for directory, dir_files in sorted(files_by_dir.items()):
                if (
                    len(files_by_dir) > 1
                ):  # Only show directory headers if multiple dirs
                    content_parts.append(f"**{directory}/**")
                content_parts.extend(
                    [
                        f"  - `{file.name}`" if len(files_by_dir) > 1 else f"- `{file}`"
                        for file in dir_files
                    ]
                )

            content = "\n".join(content_parts)
        else:
            content = "No files changed"

        self.sections.append(
            PromptSection(title="Changed Files", content=content, level=2)
        )

    def add_diff(self, diff_text: str, max_chars: int) -> None:
        if max_chars and len(diff_text) > max_chars:
            diff_text = self._truncate_diff(diff_text, max_chars)

        content = (
            f"```diff\n{diff_text if diff_text else '# No changes to display'}\n```"
        )

        self.sections.append(PromptSection(title="Changes", content=content, level=2))

    def add_context_file(self, file_path: Path, content: str) -> None:
        """Add a context file section."""
        content_md = self.get_markdown_content(file_path, content)

        self.sections.append(
            PromptSection(
                title=f"Context: `{file_path}`",
                content=content_md,
                level=3,
            )
        )

    def get_markdown_content(self, file_path: Path, content: str) -> str:
        extension = file_path.suffix[1:]
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

    @staticmethod
    def _truncate_diff(diff_text: str, max_chars: int) -> str:
        """
        Truncate diff intelligently, keeping both start and end.

        Args:
            diff_text: Original diff text.
            max_chars: Maximum characters to keep.

        Returns:
            Truncated diff with ellipsis marker.
        """
        if len(diff_text) <= max_chars:
            return diff_text

        # Try to truncate at file boundaries if possible
        half = max_chars // 2

        # Find a good break point near the middle
        truncation_marker = "\n\n... [Diff truncated for brevity] ...\n\n"

        # Look for file boundary markers near the truncation points
        start_chunk = diff_text[:half]
        end_chunk = diff_text[-half:]

        # Try to find the last complete file diff in start chunk
        if "\ndiff --git" in start_chunk:
            last_file_start = start_chunk.rfind("\ndiff --git")
            if last_file_start > half * 0.7:  # Don't go too far back
                start_chunk = start_chunk[:last_file_start]

        # Try to find the first complete file diff in end chunk
        if "diff --git" in end_chunk:
            first_file_start = end_chunk.find("diff --git")
            if first_file_start < half * 0.3:  # Don't skip too much
                end_chunk = end_chunk[first_file_start:]

        return start_chunk + truncation_marker + end_chunk
