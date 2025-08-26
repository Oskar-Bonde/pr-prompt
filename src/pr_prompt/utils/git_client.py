from pathlib import Path
from typing import Optional

from git import Blob, Diff, DiffIndex, Repo


class GitClient:
    def __init__(
        self,
        base_ref: str,
        head_ref: Optional[str] = None,
        *,
        repo_path: Optional[str] = None,
        remote: str = "origin",
    ):
        """Initialize GitClient with a repository path."""
        self.repo = Repo(repo_path)
        self.remote = self.repo.remote(remote)

        self.base_ref = base_ref
        self.head_ref = head_ref or self.repo.active_branch.name
        self.target_commit = self.repo.commit(base_ref)
        self.feature_commit = self.repo.commit(head_ref)

    def fetch_branch(self, branch: str) -> None:
        """Fetch a specific branch from a remote."""
        branch_ref = branch.removeprefix(f"{self.remote.name}/")
        if branch:
            self.remote.fetch(branch_ref)

    def get_commit_messages(self) -> list[str]:
        """Get list of commit messages between two refs."""
        commits = self.repo.iter_commits(f"{self.target_commit}..{self.feature_commit}")
        return [
            ". ".join(commit.message.strip().split("\n"))
            for commit in commits
            if isinstance(commit.message, str)
        ]

    def get_repo_name(self) -> str:
        return Path(self.repo.working_dir).name

    def list_files(self, ref: str) -> list[str]:
        """List all files in the repository at a specific ref."""
        commit = self.repo.commit(ref)
        return [
            str(item.path) for item in commit.tree.traverse() if isinstance(item, Blob)
        ]

    def get_file_content(self, ref: str, file_path: str) -> str:
        commit = self.repo.commit(ref)
        blob = commit.tree[file_path]
        blob_data: bytes = blob.data_stream.read()
        return blob_data.decode("utf-8", errors="replace").strip()

    def get_diff_index(self, context_lines: int = 999999) -> DiffIndex[Diff]:
        return self.target_commit.diff(
            self.feature_commit,
            create_patch=True,
            unified=context_lines,
            diff_algorithm="histogram",
            find_renames=50,
            function_context=True,
        )
