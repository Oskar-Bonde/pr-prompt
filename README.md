# pr-prompt

Generate structured prompts for LLM-powered pull request reviews and descriptions.

`pr-prompt` analyzes git diffs, commit messages, and file changes to create comprehensive prompts that help Large Language Models provide better code reviews and generate meaningful pull request descriptions.

## Features

- 🔍 **Smart Diff Analysis** - Analyzes git diffs with configurable context
- 📁 **File Tree Visualization** - Shows changed files in a clear tree structure
- 🎯 **Context-Aware** - Includes relevant documentation and context files
- 🚫 **Flexible Filtering** - Exclude files with blacklist patterns
- 📝 **Multiple Prompt Types** - Generate prompts for reviews, descriptions, or custom tasks
- ⚡ **Easy Integration** - Simple Python API for automation

## Installation

```bash
pip install pr-prompt
```

### Requirements

`pr-prompt` uses GitPython for git operations. GitPython needs the git executable to be installed on the system and available in your PATH. If it is not in your PATH, you can help GitPython find it by setting the `GIT_PYTHON_GIT_EXECUTABLE=<path/to/git>` environment variable.

## Quick Start

```python
from pr_prompt import PrPromptGenerator

# Create a generator with default settings
generator = PrPromptGenerator()

# Generate a code review prompt
review_prompt = generator.generate_review(
    target_branch="origin/main",
    feature_branch="feature/auth-system",
    pr_title="Add OAuth2 authentication",
    pr_description="Implements secure user authentication with JWT tokens"
)

print(review_prompt)
```

## Usage

### Basic Review Generation

```python
from pr_prompt import PrPromptGenerator

generator = PrPromptGenerator()

# Generate a prompt for reviewing changes against main branch
prompt = generator.generate_review(
    target_branch="origin/main",
    pr_title="Fix user authentication bug",
    pr_description="Resolves issue where users couldn't log in with special characters"
)
```

### Generate PR Descriptions

```python
# Generate a prompt to help write PR descriptions
description_prompt = generator.generate_description(
    target_branch="origin/main",
    feature_branch="feature/user-dashboard",
    pr_title="Add user dashboard"
)
```

### Custom Prompts

```python
# Create custom prompts with specific instructions
custom_prompt = generator.generate_custom(
    instructions="Focus on security vulnerabilities and performance issues.",
    target_branch="origin/main",
    feature_branch="feature/payment-processing"
)
```

### Configuration Options

```python
generator = PrPromptGenerator(
    # Exclude certain file types from diff analysis
    blacklist_patterns=["*.lock", "*.generated.py", "node_modules/*"],
    
    # Include context files that provide additional information
    context_patterns=["docs/architecture.md", ".github/copilot-instructions.md"],
    
    # Number of context lines around changes (default: full file)
    diff_context_lines=10,
    
    # Include commit messages in the prompt
    include_commit_messages=True
)
```

## API Reference

### PrPromptGenerator

The main class for generating pull request prompts.

#### Parameters

- `blacklist_patterns` (list[str]): File patterns to exclude from diff analysis. Default: `["*.lock"]`
- `context_patterns` (list[str]): Patterns to select context files to include. Default: `["LLM.md"]`
- `diff_context_lines` (int): Number of context lines around changes. Default: `999999` (full file)
- `include_commit_messages` (bool): Whether to include commit messages. Default: `True`

#### Methods

##### `generate_review(target_branch, feature_branch=None, *, pr_title=None, pr_description=None)`

Generates a prompt optimized for code review with instructions to:
- Identify bugs, security issues, and performance problems
- Suggest improvements and best practices
- Assess code clarity and complexity
- Provide specific, actionable feedback

##### `generate_description(target_branch, feature_branch=None, pr_title=None)`

Generates a prompt for creating comprehensive PR descriptions that:
- Summarize what the PR accomplishes
- Explain the context and reasoning
- Document impact and affected areas
- Highlight breaking changes

##### `generate_custom(instructions, target_branch, feature_branch=None, *, pr_title=None, pr_description=None)`

Generates a prompt with custom instructions for specialized use cases.

## Example Output

The generated prompts include:

1. **Instructions** - Clear guidance for the LLM
2. **Pull Request Details** - Repository info, branches, title, description, and commits
3. **Context Files** - Relevant documentation and configuration files
4. **Changed Files** - Tree view of all modified files
5. **File Diffs** - Detailed diffs for each changed file

## Advanced Usage

### Working with Different Branches

```python
# Compare feature branch against develop instead of main
prompt = generator.generate_review(
    target_branch="origin/develop",
    feature_branch="feature/new-api"
)

# Use current branch as feature branch (default behavior)
prompt = generator.generate_review(target_branch="origin/main")
```

### Including Documentation

```python
# Include specific documentation files for context
generator = PrPromptGenerator(
    context_patterns=[
        "docs/coding-standards.md",
        "CONTRIBUTING.md", 
        ".github/pull_request_template.md"
    ]
)
```

### Filtering Large Files

```python
# Exclude generated files and large assets
generator = PrPromptGenerator(
    blacklist_patterns=[
        "*.lock",
        "*.min.js",
        "*.bundle.*",
        "dist/*",
        "build/*",
        "*.generated.*"
    ]
)
```

## Integration Examples

### GitHub Actions

```yaml
name: Generate PR Review Prompt
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  generate-prompt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install pr-prompt
      
      - name: Generate review prompt
        run: |
          python -c "
          from pr_prompt import PrPromptGenerator
          generator = PrPromptGenerator()
          prompt = generator.generate_review('origin/main')
          print(prompt)
          "
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-push

python -c "
from pr_prompt import PrPromptGenerator
generator = PrPromptGenerator()
prompt = generator.generate_review('origin/main')
print('Review prompt generated successfully!')
"
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to our GitHub repository.