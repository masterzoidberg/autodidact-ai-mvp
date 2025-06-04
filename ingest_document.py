"""Utility functions for ingesting documents into text or Markdown.

This module provides a simple interface for saving string content to a
specified file while allowing control over the output format.
"""

from pathlib import Path


def ingest_document(content: str, output_path: str, output_format: str | None = None) -> Path:
    """Save *content* to *output_path* in the desired *output_format*.

    Parameters
    ----------
    content : str
        The text content to write out.
    output_path : str
        Destination file path. If *output_format* is ``None`` the file
        extension of this path determines the format.
    output_format : {"txt", "md"}, optional
        Desired output format. If provided, this extension overrides the
        one inferred from *output_path*.

    Returns
    -------
    pathlib.Path
        The path to the written file.
    """
    path = Path(output_path)

    # Determine extension
    ext = output_format or path.suffix.lstrip(".") or "txt"
    if ext not in {"txt", "md"}:
        raise ValueError("output_format must be 'txt' or 'md'")

    # Ensure path has the correct suffix
    path = path.with_suffix(f".{ext}")

    path.write_text(content, encoding="utf-8")
    return path
