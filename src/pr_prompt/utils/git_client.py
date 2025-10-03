from pathlib import Path
from typing import Optional

from git import Blob, Diff, DiffIndex, Repo


class GitClient:
    def __init__(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        *,
        repo_path: Optional[str] = None,
        remote: str = "origin",
    ):
        """Initialize GitClient with a repository path."""
        self.repo = Repo(repo_path)
        self.remote = self.repo.remote(remote)

        self.base_ref = base_ref or self.get_default_branch()
        self.head_ref = head_ref or self.repo.active_branch.name

        self.base_commit = self.repo.commit(self.base_ref)
        self.head_commit = self.repo.commit(self.head_ref)

    def get_default_branch(self) -> str:
        """Get the default branch name from the remote."""
        try:
            remote_head = self.remote.refs.HEAD
            default_branch = remote_head.reference.remote_head  # type: ignore[attr-defined]
            return f"{self.remote.name}/{default_branch}"  # noqa: TRY300
        except (AttributeError, IndexError) as err:
            # Fallback to common default branch names
            for branch_name in ["main", "master"]:
                if f"{self.remote.name}/{branch_name}" in [
                    ref.name for ref in self.remote.refs
                ]:
                    return f"{self.remote.name}/{branch_name}"
            msg = "Could not determine default branch. Please specify base_ref."
            raise InferBaseBranchError(msg) from err

    def fetch_base_branch(self) -> None:
        """Fetch the base ref if it's a remote branch."""
        if self.base_ref.startswith(f"{self.remote.name}/"):
            ref = self.base_ref.removeprefix(f"{self.remote.name}/")
            self.remote.fetch(ref)

    def get_commit_messages(self) -> list[str]:
        """Get list of commit messages between two refs."""
        commits = self.repo.iter_commits(f"{self.base_commit}..{self.head_commit}")
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
        return self.base_commit.diff(
            self.head_commit,
            create_patch=True,
            unified=context_lines,
            diff_algorithm="histogram",
            find_renames=50,
            function_context=True,
        )


class InferBaseBranchError(Exception):
    """Raised when unable to infer the default branch from the remote."""
