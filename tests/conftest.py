"""Shared test fixtures and utilities."""

from typing import Optional
from unittest.mock import MagicMock

import pytest
from git import Diff, DiffIndex

from pr_prompt.utils import GitClient


@pytest.fixture
def mock_git_client() -> MagicMock:
    """Create a basic mock GitClient fixture."""
    return create_mock_git_client()


def create_mock_git_client(
    target_branch: str = "main",
    feature_branch: str = "feature/test",
    *,
    repo_name: str = "test-repo",
    files: Optional[list[str]] = None,
    commit_messages: Optional[list[str]] = None,
) -> MagicMock:
    """
    Create a properly configured mock GitClient.

    Args:
        target_branch: Target branch name
        feature_branch: Feature branch name
        repo_name: Repository name
        files: List of files in the repository
        commit_messages: List of commit messages
        diff_content: Custom diff content for the mock diff

    Returns:
        Configured MagicMock instance
    """
    if files is None:
        files = ["main.py"]
    if commit_messages is None:
        commit_messages = ["Initial commit"]

    mock_git = MagicMock(spec=GitClient)
    mock_git.target_branch = target_branch
    mock_git.feature_branch = feature_branch
    mock_git.get_repo_name.return_value = repo_name
    mock_git.list_files.return_value = files
    mock_git.get_commit_messages.return_value = commit_messages
    mock_git.fetch_branch.return_value = None
    mock_git.get_file_content.return_value = "context file content"

    # Create mock diff index with proper structure
    mock_diffs = []
    for file in files:
        mock_diff = create_mock_diff(file)
        mock_diffs.append(mock_diff)

    mock_diff_index = MagicMock(spec=DiffIndex)
    mock_diff_index.__iter__ = MagicMock(return_value=iter(mock_diffs))

    mock_git.get_diff_index.return_value = mock_diff_index

    return mock_git


def create_mock_diff(
    file_path: str,
    change_type: str = "modified",
    diff_content: Optional[str] = None,
) -> MagicMock:
    """
    Create a mock Diff object.

    Args:
        file_path: Path to the file
        change_type: Type of change (added, deleted, modified, renamed)
        diff_content: Custom diff content

    Returns:
        Configured mock Diff object
    """
    if diff_content is None:
        diff_content = f"@@ -1,1 +1,2 @@\n+new content in {file_path}"

    mock_diff = MagicMock(spec=Diff)
    mock_diff.a_path = file_path
    mock_diff.b_path = file_path

    # Set change type flags
    mock_diff.new_file = change_type == "added"
    mock_diff.deleted_file = change_type == "deleted"
    mock_diff.copied_file = change_type == "copied"
    mock_diff.renamed_file = change_type == "renamed"
    mock_diff.rename_from = None
    mock_diff.rename_to = None

    if change_type == "renamed":
        mock_diff.rename_from = file_path
        mock_diff.rename_to = file_path.replace("old_", "new_")
        mock_diff.b_path = mock_diff.rename_to

    mock_diff.diff = diff_content.encode()

    return mock_diff
