# pr-prompt

Generate pull request prompts (review, description, or custom) from git diffs, commits, and context files.

## 🚀 Features

### 🤖 Pull Request Prompt
- **Prompt Instructions**: Generate review or description prompts, or supply custom instructions.
- **Diff**: Display differences between the current and base branches.
- **Context Patterns**: Include matched files in the prompt for additional context.
- **Blacklist Patterns**: Exclude noisy files (e.g., `*.lock`).
- **Overview**: Get PR metadata, context files, and changed file tree without diffs.
- **File Diff**: Get diffs for specific files using glob patterns.

### 🛠️ Usage & Integration
- **Python API**: Usable as a library in your own tools.
- **CLI Interface**: Simple command-line for quick use.
- **TOML Configuration**: Configure via `pyproject.toml`.
- **Vendor Agnostic**: Works with any LLM.


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
# Full review prompt (default type) to stdout
pr-prompt generate

# Full description prompt to stdout
pr-prompt generate description

# Custom prompt (requires custom_instructions in TOML config)
pr-prompt generate custom

# Copy review prompt to clipboard
pr-prompt generate review | xclip -selection clipboard

# PR overview: metadata + context files + changed file tree (no diffs)
pr-prompt overview

# File diffs for specific glob patterns
pr-prompt diff 'src/*.py'
pr-prompt diff '*.py' '*.md'
```

### 🔗 Shell Aliases
Add to your shell config (e.g., `~/.bashrc` or `~/.zshrc`):
```bash
alias review='uvx pr-prompt generate review | xclip -selection clipboard'
alias desc='uvx pr-prompt generate description | xclip -selection clipboard'
```

## ⚙️ Configuration

### 🔧 Parameters Reference
PrPromptGenerator / CLI / TOML shared parameters:
- `blacklist_patterns` `(list[str])` File patterns to exclude from diffs and context file inclusion. Default: `["*.lock", "package-lock.json"]`. Note: binary files are automatically detected and excluded.
- `context_patterns` `(list[str] | None)` File patterns to include in prompt (after blacklist filtering). Default: `None`
- `fetch_base` `(bool)` Fetch base ref before generating diff. Default: `False`
- `diff_context_lines` `(int)` Number of context lines around changes in diffs. Default: `999999`
- `include_commit_messages` `(bool)` Include commit messages in prompt. Default: `True`
- `repo_path` `(str | None)` Target repo path. Default: `cwd`
- `remote` `(str)` Git remote name. Default: `origin`
- `default_base_branch` `(str | None)` Used when base_ref not passed. Inferred if omitted.
- `custom_instructions` `(str | None)` Used when `instructions` are not provided in generate_custom.

### 📜 Parameter Precedence Order
Highest wins (later overrides earlier):
1. Internal defaults (dataclass field defaults)
2. pyproject.toml / pr_prompt.toml [tool.pr-prompt] values
3. Explicit constructor args / CLI flags (mapped to generator args)
4. Per-call method arguments (e.g., base_ref passed to generate_review)

Notes:
- If you call `generate_review(base_ref=...)`, that overrides both default_base_branch and any TOML value.
- For `custom` prompts: if `instructions` arg omitted, `custom_instructions` (TOML or constructor) must be set or an error is raised.

## 🎯 Prompt Types

### 🔍 Review
Guides the LLM to write a code review (quality, correctness, security, performance, clarity).

### 📝 Description
Guides the LLM to write a clear PR description (summary, rationale, impact).

### 🛠️ Custom
Arbitrary instructions. Requires:
- Pass `instructions=...` in `generate_custom`, OR
- Set `custom_instructions` in constructor/TOML (used when CLI type=custom)

## 📄 Prompt Example
```markdown
## Instructions
You are a senior software engineer...

## Pull Request Details
Repository: pr-prompt
Branch: `feature` -> `origin/main`
Commits: Bumped minor

## Context Files
File: `README.md`...

## Changed Files
M src/pr_prompt/__init__.py

## File diffs
Modified `src/pr_prompt/__init__.py`
~~~diff
-__version__ = "0.3.0"
+__version__ = "0.4.0"
~~~
```

## ⚙️ Using pyproject.toml / pr_prompt.toml

### 🔧 Default Configuration
```toml
[tool.pr-prompt]
blacklist_patterns = ["*.lock", "package-lock.json"]
# context_patterns =
fetch_base = false
diff_context_lines = 999999
include_commit_messages = true
# repo_path =
remote = "origin"
# default_base_branch =
# custom_instructions =
```

## 🤝 Contributing
Contributions welcome. Please open issues / PRs.

## 📜 License
MIT License (see LICENSE).