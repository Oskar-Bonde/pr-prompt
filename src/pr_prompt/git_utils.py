import subprocess
from typing import Optional


class GitClient:
    @staticmethod
    def run(*args: str) -> str:
        """Run a git command and return its output."""
        try:
            result = subprocess.run(  # noqa: S603
                ["git", *args],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            msg = f"Git command failed: git {' '.join(args)}\n{e.stderr}"
            raise GitError(msg) from e

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        return self.run("rev-parse", "--abbrev-ref", "HEAD")

    def fetch_branch(self, branch: str) -> None:
        """Fetch a specific branch from a remote."""
        remote, branch_ref = self._parse_branch(branch)
        if remote:
            self.run("fetch", remote, branch_ref)

    def _parse_branch(self, branch: str) -> tuple[Optional[str], str]:
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
        return None, branch

    def get_commit_messages(self, target_branch: str, feature_branch: str) -> list[str]:
        """Get list of commit messages between two refs."""
        output = self.run(
            "log", "--pretty=format:%s", f"{target_branch}..{feature_branch}"
        )
        return output.splitlines() if output else []

    def list_files(self, ref: str) -> list[str]:
        """List all files in the repository at a specific ref."""
        output = self.run("ls-tree", "-r", "--name-only", ref)
        return output.splitlines() if output else []

    def get_file_content(self, ref: str, file_path: str) -> str:
        return self.run("show", f"{ref}:{file_path}")

    def get_changed_files(self, target_branch: str, feature_branch: str) -> list[str]:
        output = self.run("diff", "--name-only", f"{target_branch}...{feature_branch}")
        return output.splitlines() if output else []

    def get_diff(
        self,
        target_branch: str,
        feature_branch: str,
        context_lines: int,
    ) -> str:
        return self.run(
            "diff",
            f"--unified={context_lines}",
            "--diff-algorithm=histogram",
            "--function-context",
            "--find-renames=50",
            f"{target_branch}...{feature_branch}",
        )


class GitError(Exception):
    """Raised when a git command fails."""
