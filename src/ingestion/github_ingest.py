"""GitHub repository and local repository ingestion engine."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests


def scan_directory_tree(
    root_path: Path, max_depth: int = 3, max_files: int = 150
) -> Dict[str, Any]:
    """Inspects repo directory tree, ignoring vendor/build caches."""
    ignore_dirs = {
        ".git",
        "node_modules",
        "vendor",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        "target",
        ".cache",
    }
    ignore_exts = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".mp4",
        ".mp3",
        ".wav",
        ".zip",
        ".tar",
        ".gz",
        ".lock",
        ".pyc",
    }

    tree_entries = []
    file_count = 0
    key_files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".")]

        rel_dir = os.path.relpath(dirpath, root_path)
        depth = 0 if rel_dir == "." else len(Path(rel_dir).parts)
        if depth > max_depth:
            continue

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in ignore_exts:
                continue

            rel_file = fname if rel_dir == "." else os.path.join(rel_dir, fname)
            tree_entries.append(rel_file)
            file_count += 1

            # Priority files
            lower = fname.lower()
            if lower in ["readme.md", "architecture.md", "cargo.toml", "package.json", "pyproject.toml", "main.py", "main.go", "index.ts", "server.js"]:
                key_files.append(rel_file)

            if file_count >= max_files:
                break
        if file_count >= max_files:
            break

    return {
        "files": tree_entries,
        "key_files": key_files,
        "file_count": file_count,
    }


def extract_key_source_snippets(
    root_path: Path, key_files: List[str], max_snippets: int = 5, max_chars_per_snippet: int = 1200
) -> List[Dict[str, str]]:
    """Extracts illustrative source code from key files."""
    snippets = []
    for rel_path in key_files:
        full_path = root_path / rel_path
        if not full_path.is_file():
            continue
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_chars_per_snippet)
                snippets.append({
                    "file": rel_path,
                    "content": content,
                })
        except Exception:
            continue
        if len(snippets) >= max_snippets:
            break
    return snippets


def ingest_github_url(url: str, temp_dir: Path) -> Dict[str, Any]:
    """Ingests remote GitHub repo using sparse/shallow clone or GitHub raw API."""
    import subprocess
    clean_url = url.strip().rstrip("/")
    repo_name = clean_url.split("/")[-1].replace(".git", "")
    target_dir = temp_dir / repo_name

    if not target_dir.exists():
        # Shallow clone depth 1 to save disk & time
        cmd = ["git", "clone", "--depth", "1", clean_url, str(target_dir)]
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)

    tree_info = scan_directory_tree(target_dir)
    snippets = extract_key_source_snippets(target_dir, tree_info["key_files"])

    readme_content = ""
    for kf in tree_info["key_files"]:
        if "readme" in kf.lower():
            try:
                with open(target_dir / kf, "r", encoding="utf-8", errors="ignore") as f:
                    readme_content = f.read(4000)
            except Exception:
                pass
            break

    return {
        "title": repo_name,
        "source_type": "github",
        "url": clean_url,
        "tree": tree_info["files"][:40],
        "readme_excerpt": readme_content,
        "snippets": snippets,
    }
