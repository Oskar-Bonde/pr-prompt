"""Git command utilities."""

import subprocess
from pathlib import Path


class GitClient:
    """Wrapper for git operations."""

    @staticmethod
    def run(*args: str) -> str:
        """Run a git command and return its output."""
        try:
            result = subprocess.run(
                ["git", *args], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            msg = f"Git command failed: git {' '.join(args)}\n{e.stderr}"
            raise GitError(msg) from e

    def fetch_branch(self, branch: str) -> None:
        """Fetch a specific branch from a remote."""
        remote, branch_ref = self._parse_branch(branch)
        self.run("fetch", remote, branch_ref)

    def _parse_branch(self, branch: str) -> tuple[str, str]:
        """
        Parse a branch reference into remote and branch name.

        Args:
            branch: Branch reference (e.g., 'origin/main' or 'main').

        Returns:
            Tuple of (remote, branch) or ('', branch) if no remote.
        """
        if "/" in branch:
            branch_parts = branch.split("/", 1)
            if branch_parts[0] in ["origin", "upstream"]:
                return branch_parts[0], branch_parts[1]
        return "", branch

    def get_changed_files(self, target_branch: str, feature_branch: str) -> list[Path]:
        """
        Get list of files changed between two refs.

        Args:
            target_branch: Base reference (e.g., 'origin/main').
            feature_branch: Head reference (e.g., 'feature-branch').

        Returns:
            list of changed file paths.
        """
        output = self.run("diff", "--name-only", f"{target_branch}...{feature_branch}")
        changed_files = output.splitlines() if output else []
        return [Path(file) for file in changed_files]

    def get_diff(
        self,
        target_branch: str,
        feature_branch: str,
        file_whitelist: list[Path],
    ) -> str:
        """
        Get git diff between two refs.

        Args:
            target_branch: Base reference.
            feature_branch: Head reference.
            file_whitelist: Whitelist of specific files to diff.
        """
        if not file_whitelist:
            return ""

        cmd = [
            "diff",
            "--unified=999999",
            "--diff-algorithm=histogram",
            "--function-context",
            f"{target_branch}...{feature_branch}",
            "--",
        ]
        cmd.extend([str(file) for file in file_whitelist])

        return self.run(*cmd)

    def list_files(self, ref: str) -> list[str]:
        """List all files in the repository at a specific ref."""
        output = self.run("ls-tree", "-r", "--name-only", ref)
        return output.splitlines() if output else []

    def get_file_content(self, ref: str, file_path: str) -> str:
        return self.run("show", f"{ref}:{file_path}")


class GitError(Exception):
    """Raised when a git command fails."""
