"""Generator for pull request prompts."""

from dataclasses import dataclass, field
from typing import Optional

from .markdown_builder import MarkdownBuilder
from .utils import GitClient, get_diff_files


@dataclass
class PrPromptGenerator:
    """
    Generator for pull request prompts.

    This class creates formatted prompts for pull requests using `git diff`.

    Example:
        ```python
        generator = PrPromptGenerator(
            blacklist_patterns=["*.lock"],
            context_patterns=["AGENTS.md"],
            include_commit_messages=True,
        )
        prompt = generator.generate(
            base_ref="origin/main",
            head_ref=None,
            pr_title="Add new authentication system",
            pr_description="Implements OAuth2 with JWT tokens",
        )
        ```

    Attributes:
        blacklist_patterns: File patterns to exclude from the diff analysis.
            Default: `["*.lock"]`.
        context_patterns: Patterns to select context files to include in prompt.
            Useful for including documentation that provide context for the review.
            Default: `["AGENTS.md"]`.
        diff_context_lines: Number of context lines around changes in diffs.
            Default: `999999`.
        include_commit_messages: Whether to include commit messages in the prompt.
            Default: `True`.
        repo_path: The path to either the worktree directory or the .git directory itself.
            Default: Current working directory.
        remote: Name of the git remote to use.
            Default: `"origin"`.
    """

    blacklist_patterns: list[str] = field(default_factory=lambda: ["*.lock"])
    context_patterns: list[str] = field(default_factory=lambda: ["AGENTS.md"])

    diff_context_lines: int = 999999
    include_commit_messages: bool = True
    repo_path: Optional[str] = None
    remote: str = "origin"

    def generate_review(
        self,
        base_ref: str,
        head_ref: Optional[str] = None,
        *,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
    ) -> str:
        """
        Generate a prompt for reviewing a pull request.

        Args:
            base_ref: The base branch/commit to compare against (e.g., "origin/main").
            head_ref: The branch/commit with changes.
                Default: current branch.
            pr_title: The title of the pull request.
            pr_description: The description of the pull request.
        """
        instructions = """You are an expert software engineer reviewing a pull request.

Your task:
- Identify Issues: Find potential bugs, security vulnerabilities, and performance problems
- Suggest Improvements: Recommend refactorings and best practices
- Assess Clarity: Point out unclear or overly complex code
- Be Specific: Reference line numbers and provide concrete examples

Focus on actionable feedback that improves code quality and maintainability."""
        return self._generate(
            instructions,
            base_ref,
            head_ref,
            pr_title=pr_title,
            pr_description=pr_description,
        )

    def generate_description(
        self,
        base_ref: str,
        head_ref: Optional[str] = None,
        pr_title: Optional[str] = None,
    ) -> str:
        """Generate a prompt for creating PR descriptions."""
        instructions = """You are an expert software engineer writing a pull request description.

Your task:
- Summarize Changes: Describe what this PR accomplishes
- Explain Context: Why these changes were needed
- Document Impact: What areas of the codebase are affected
- Note Breaking Changes: Highlight any breaking changes or migration steps
- Be Clear: Write for other developers who will review and maintain this code

Create a clear, comprehensive PR description that helps reviewers understand the changes."""
        return self._generate(
            instructions,
            base_ref,
            head_ref,
            pr_title=pr_title,
            pr_description=None,
        )

    def generate_custom(
        self,
        instructions: str,
        base_ref: str,
        head_ref: Optional[str] = None,
        *,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
    ) -> str:
        """Generate a pull request prompt with custom instructions."""
        return self._generate(
            instructions,
            base_ref,
            head_ref,
            pr_title=pr_title,
            pr_description=pr_description,
        )

    def _generate(
        self,
        instructions: str,
        base_ref: str,
        head_ref: Optional[str] = None,
        *,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
    ) -> str:
        """Generate a pull request prompt."""
        git = GitClient(
            base_ref, head_ref, repo_path=self.repo_path, remote=self.remote
        )

        git.fetch_branch(base_ref)

        builder = MarkdownBuilder(git)

        builder.add_instructions(instructions)

        builder.add_metadata(
            include_commit_messages=self.include_commit_messages,
            pr_title=pr_title,
            pr_description=pr_description,
        )

        builder.add_context_files(self.context_patterns)

        diff_index = git.get_diff_index(self.diff_context_lines)

        builder.add_changed_files(diff_index)

        diff_files = get_diff_files(diff_index, self.blacklist_patterns)
        builder.add_file_diffs(diff_files)

        return builder.build()
