"""Fail when the public toolkit contains common private-artifact signatures."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "build", "dist", "__pycache__"}
TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml", ".cff"}
PATTERNS = {
    "absolute_user_path": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "credential_assignment": re.compile(
        r"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]+"
    ),
    "clinical_identifier": re.compile(r"(?i)\b(?:medical[_ -]?record|patient[_ -]?id|mrn)\b"),
}


def main() -> None:
    findings = []
    # Everything git could commit: tracked files plus untracked ones not covered by .gitignore.
    listed = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    ).decode("utf-8").split("\0")
    for path in (ROOT / name for name in listed if name):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            # Binary or unknown files (xlsx, zip, parquet, ...) cannot be scanned, so they are refused.
            findings.append(f"{path.relative_to(ROOT)}: unscannable_file_type")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(ROOT)}:{line}: {name}")
    if findings:
        raise SystemExit("public safety scan failed:\n" + "\n".join(findings))
    print("public safety scan passed")


if __name__ == "__main__":
    main()
