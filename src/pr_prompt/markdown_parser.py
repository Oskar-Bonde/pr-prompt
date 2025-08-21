from pathlib import Path


def get_markdown_content(file_path: str, content: str) -> str:
    extension = Path(file_path).suffix[1:]
    lang_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "jsx": "jsx",
        "tsx": "tsx",
        "java": "java",
        "go": "go",
        "rs": "rust",
        "cpp": "cpp",
        "c": "c",
        "cs": "csharp",
        "rb": "ruby",
        "php": "php",
        "swift": "swift",
        "kt": "kotlin",
        "scala": "scala",
        "sh": "bash",
        "yml": "yaml",
        "yaml": "yaml",
        "json": "json",
        "xml": "xml",
        "html": "html",
        "css": "css",
        "sql": "sql",
        "md": "markdown",
    }
    lang = lang_map.get(extension, "text")

    if lang == "markdown":
        content = f"~~~{lang}\n{content}\n~~~"
    else:
        content = f"```{lang}\n{content}\n```"
    return content
