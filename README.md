# pr-prompt

Generate pull request prompts (review, description, or custom) from git diffs, commits, and context files.

## 🚀 Features

### 🤖 Prompt Generation
- 🔍 **Diff** - Show difference between current and base branch.
- 📝 **Multiple Prompt Types**: `review`, `description`, and `custom`.
- 📁 **Files Tree** - Displays a tree of changed files.
- 🚫 **Blacklist Patterns** - Exclude noisy files like `*.lock`.
- 📚 **Context Patterns** - Include any file in prompt for context.

### 🛠️ Usage & Integration
- 🐍 **Python API**: Usable as a library in your own tools.
- 🖥️ **CLI Interface**: Simple command-line for quick use.
- ⚙️ **TOML Configuration**: Configure via `pyproject.toml`.
- 👤 **Vendor Agnostic**: Works with any LLM.


## 📥 Installation
```bash
pip install pr-prompt
```

### 📚 Requirements
- Python 3.9+
- git installed and on PATH (or set GIT_PYTHON_GIT_EXECUTABLE)

## ⚡ Quick Start

### 🐍 Python API (PrPromptGenerator)
```python
from pr_prompt import PrPromptGenerator

generator = PrPromptGenerator.from_toml()  # uses defaults + any TOML config
prompt = generator.generate_review()       # compares current HEAD to default base branch
print(prompt)
```

### 🖥️ CLI Usage
```bash
# Review prompt (default type) to stdout
pr-prompt

# Review prompt saved to .pr_prompt/review.md
pr-prompt review --write

# Description prompt to stdout
pr-prompt description -b main

# Custom prompt (requires custom_instructions in TOML config)
pr-prompt custom
```
Outputs to stdout by default. Use `--write` to save to `.pr_prompt/<type>.md`.

Flags:
- `--base-ref / -b` base branch or commit
- `--blacklist` repeatable pattern exclusion
- `--context` repeatable pattern inclusion
- `--write` save to `.pr_prompt/<type>.md` instead of stdout

## ⚙️ Configuration

### 🔧 Parameters Reference
PrPromptGenerator / CLI / TOML shared parameters:
- `blacklist_patterns` `(list[str])` File patterns to exclude from diff. Default: `["*.lock"]`
- `context_patterns` `(list[str])` File patterns to include in prompt. Used for including documentation that provides context. Default: `["AGENTS.md"]`
- `diff_context_lines` `(int)` Number of context lines around changes in diffs. Default: `999999`
- `include_commit_messages` `(bool)` Include commit messages in prompt. Default: `True`
- `repo_path` `(str | None)` Target repo path. Default: `cwd`
- `remote` `(str)` Git remote name. Default: `origin`
- `default_base_branch` `(str | None)` Used when base_ref not passed. Inferred if omitted.
- `custom_instructions` `(str | None)` Used when `instructions` are not provided in generate_custom.
- `fetch_base` `(bool)` Fetch base ref before generating diff. Default: `True`

### 📜 Parameter Precedence Order
Highest wins (later overrides earlier):
1. Internal defaults (dataclass field defaults)
2. pyproject.toml / pr_prompt.toml [tool.pr-prompt] values
3. Explicit constructor args / CLI flags (mapped to generator args)
4. Per-call method arguments (e.g., base_ref passed to generate_review)
Notes:
- If you call `generate_review(base_ref=...)`, that overrides both default_base_branch and any TOML value.
- For CUSTOM prompts: if `instructions` arg omitted, `custom_instructions` (TOML or constructor) must be set or an error is raised.

## 🎯 Prompt Types

### 🔍 Review
Guides the LLM to write a code review (quality, correctness, security, performance, clarity).

### 📝 Description
Guides the LLM to write a clear PR description (summary, rationale, impact).

### 🛠️ Custom
Arbitrary instructions. Requires:
- Pass `instructions=...` in `generate_custom`, OR
- Set `custom_instructions` in constructor/TOML (used when CLI type=custom)

## 📋 Prompt Structure
Generated Markdown sections:
- Instructions: Role plus review / description / custom goals.
- Pull Request Details: Repository name, base -> head branch, optional description, commit list.
- Context Files: Inline content from context_patterns for architectural / design background.
- Changed Files Tree: Condensed tree view of modified paths.
- File Diffs: Diffs filtered by blacklist_patterns with configured context lines.

## 📄 Prompt Example
(Review excerpt)
~~~markdown
## Instructions
You are a senior software engineer...

## Pull Request Details
**Repository:** pr-prompt
**Branch:** `feature` -> `main`
**Commits:** Bumped minor
## Changed Files
src/
└── pr_prompt/
    └── __init__.py
## File diffs
### Modified `src/pr_prompt/__init__.py`
```diff
-__version__ = "0.3.0"
+__version__ = "0.4.0"
```
~~~

## ⚙️ Using pyproject.toml / pr_prompt.toml

### 🔧 Default Configuration
```toml
[tool.pr-prompt]
blacklist_patterns = ["*.lock"]
context_patterns = ["AGENTS.md"]
diff_context_lines = 999999
include_commit_messages = true
# repo_path =
remote = "origin"
# default_base_branch =
# custom_instructions =
fetch_base = true
```

## 🤝 Contributing
Contributions welcome. Please open issues / PRs.

## 📜 License
MIT License (see LICENSE).