"""Tests for pr_prompt package."""

from unittest.mock import MagicMock, patch

from git import Repo

from pr_prompt.generator import PrPromptGenerator
from pr_prompt.markdown_builder import MarkdownBuilder
from pr_prompt.utils import FileFilter, get_diff_files
from pr_prompt.utils.git_client import GitClient

from .conftest import create_mock_git_client


class TestFileFilter:
    """Test file filtering functionality."""

    def test_match_no_patterns(self) -> None:
        """Test match with no patterns returns empty list."""
        files = ["main.py", "test.py"]
        assert FileFilter.include(files, []) == []

    def test_match_with_patterns(self) -> None:
        """Test match returns files matching patterns."""
        files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
        ]
        patterns = ["src/*.py", "*.md"]
        result = FileFilter.include(files, patterns)
        assert sorted(result) == [
            "README.md",
            "src/main.py",
            "src/utils.py",
        ]


class TestMarkdownBuilder:
    """Test prompt building functionality."""

    def test_add_metadata_with_title_only(self, mock_git_client: MagicMock) -> None:
        """Test adding metadata with description."""
        builder = MarkdownBuilder(mock_git_client)
        builder.add_metadata(
            include_commit_messages=False,
            pr_description="Fix bug in authentication",
        )

        prompt = builder.build()
        assert "Fix bug in authentication" in prompt
        assert "**Description:**" in prompt

    def test_add_changed_files(self) -> None:
        """Test changed files display."""
        files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
        ]
        mock_git = create_mock_git_client(files=files)
        builder = MarkdownBuilder(mock_git)

        diff_index = mock_git.get_diff_index()
        diff_files = get_diff_files(diff_index, [])
        builder.add_changed_files_tree(diff_files)

        prompt = builder.build()
        assert "main.py" in prompt
        assert "utils.py" in prompt
        assert "test_main.py" in prompt
        assert "README.md" in prompt

    def test_add_context_file_with_syntax_highlighting(self) -> None:
        """Test context file with appropriate syntax highlighting."""
        mock_git = create_mock_git_client(files=["main.py", "example.py"])

        builder = MarkdownBuilder(mock_git)
        builder.add_context_files(["example.py"], [], {})

        prompt = builder.build()
        assert "context file content" in prompt


class TestPrPrompt:
    """Test PR prompt generator."""

    def test_default_initialization(self) -> None:
        """Test generator initializes with defaults."""
        generator = PrPromptGenerator()
        diff_context_lines = 999999
        default_include_commit_messages = True
        assert generator.diff_context_lines == diff_context_lines
        assert generator.include_commit_messages == default_include_commit_messages

    @patch("pr_prompt.generator.GitClient")
    def test_generate(
        self,
        mock_git_client_class: MagicMock,
    ) -> None:
        """Test prompt generation."""
        # Configure the mock to return our mock instance
        files = ["main.py", "uv.lock"]
        mock_git = create_mock_git_client(
            base_ref="origin/main",
            head_ref="feature/test",
            files=files,
            commit_messages=["Initial commit"],
        )
        mock_git_client_class.return_value = mock_git

        generator = PrPromptGenerator()
        prompt = generator.generate_review(
            base_ref="origin/main",
            head_ref="feature/test",
            pr_description="Test PR",
        )
        assert "Test PR" in prompt
        assert "main.py" in prompt
        assert "File diffs" in prompt
        assert "File diffs" in prompt


class TestGitClientMergeBase:
    """Test merge-base diff behavior in GitClient."""

    @patch.object(Repo, "__init__", return_value=None)
    def test_get_diff_index_uses_merge_base(self, _mock_repo_init: MagicMock) -> None:
        """Test that get_diff_index diffs from the merge-base, not base_commit."""
        client = object.__new__(GitClient)
        client.repo = MagicMock(spec=Repo)

        merge_base_commit = MagicMock()
        client.base_commit = MagicMock()
        client.head_commit = MagicMock()
        client.repo.merge_base.return_value = [merge_base_commit]

        client.get_diff_index(context_lines=3)

        client.repo.merge_base.assert_called_once_with(
            client.base_commit, client.head_commit
        )
        merge_base_commit.diff.assert_called_once_with(
            client.head_commit,
            create_patch=True,
            unified=3,
            diff_algorithm="histogram",
            find_renames=50,
            function_context=True,
        )
        client.base_commit.diff.assert_not_called()

    @patch.object(Repo, "__init__", return_value=None)
    def test_get_diff_index_falls_back_without_merge_base(
        self, _mock_repo_init: MagicMock
    ) -> None:
        """Test fallback to base_commit when no merge-base exists."""
        client = object.__new__(GitClient)
        client.repo = MagicMock(spec=Repo)

        client.base_commit = MagicMock()
        client.head_commit = MagicMock()
        client.repo.merge_base.return_value = []

        client.get_diff_index()

        client.base_commit.diff.assert_called_once()

    @patch.object(Repo, "__init__", return_value=None)
    def test_fetch_base_branch_re_resolves_commit(
        self, _mock_repo_init: MagicMock
    ) -> None:
        """Test that fetch_base_branch updates base_commit after fetching."""
        client = object.__new__(GitClient)
        client.repo = MagicMock(spec=Repo)
        client.remote = MagicMock()
        client.remote.name = "origin"
        client.base_ref = "origin/main"

        old_commit = MagicMock()
        new_commit = MagicMock()
        client.base_commit = old_commit
        client.repo.commit.return_value = new_commit

        client.fetch_base_branch()

        client.remote.fetch.assert_called_once_with("main")
        client.repo.commit.assert_called_once_with("origin/main")
        assert client.base_commit is new_commit
