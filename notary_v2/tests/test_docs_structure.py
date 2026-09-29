import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
)
TRACKED_PATHS = set(
    subprocess.run(
        ["git", "ls-files"],
        cwd=GIT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
)
MODULE_READMES = (
    "docs/domains/inheritance/README.md",
    "docs/platform/document-intake/README.md",
    "docs/platform/case-workspace/README.md",
    "docs/platform/document-generation/README.md",
    "docs/platform/fast-text-audit/README.md",
)
LEGACY_DOC_DIRS = (
    "docs/plans",
    "docs/specs",
    "docs/issues",
    "docs/changelog",
    "docs/learning",
    "docs/research",
)

def test_required_module_readmes_exist():
    missing = [path for path in MODULE_READMES if not (ROOT / path).is_file()]
    assert missing == []

def test_legacy_document_buckets_are_gone():
    remaining = [path for path in LEGACY_DOC_DIRS if (ROOT / path).exists()]
    assert remaining == []

def test_module_readmes_declare_routing_metadata():
    for path in MODULE_READMES:
        text = (ROOT / path).read_text(encoding="utf-8")
        for field in ("Status", "Source of truth", "Read when"):
            assert re.search(rf"^{field}:\s*\S", text, re.MULTILINE), f"{path}: {field}"

def test_module_readme_markdown_targets_exist():
    for path in MODULE_READMES:
        readme = ROOT / path
        text = readme.read_text(encoding="utf-8")
        targets = set(re.findall(r"`([^`\n]+(?:\.md|/))`", text))
        targets.update(re.findall(r"\[[^\]]*\]\(([^)\s]+\.md)\)", text))
        for target in targets:
            resolved = (ROOT / target if target.startswith(("docs/", "word_templates/")) else readme.parent / target).resolve()
            assert resolved.exists(), f"{path}: missing {target}"
            relative = resolved.relative_to(GIT_ROOT).as_posix()
            tracked = relative in TRACKED_PATHS or resolved.is_dir() and any(
                path.startswith(f"{relative}/") for path in TRACKED_PATHS
            )
            assert tracked, f"{path}: untracked {target}"

def test_agents_routed_markdown_exists():
    agents_path = ROOT / "AGENTS.md"
    if not agents_path.is_file():
        # AGENTS.md is intentionally absent inside the monorepo snapshot —
        # the monorepo rule removes per-repo agent files (commit be14999).
        # The routed-SOT contract only applies when the file exists.
        import pytest

        pytest.skip("AGENTS.md absent by monorepo rule")
    agents = agents_path.read_text(encoding="utf-8")
    section = re.search(
        r"^## 2\. Nguồn chuẩn và tài liệu tham chiếu[ \t]*\n(?P<body>.*?)(?=^## 3\. Tra cứu mã\b)",
        agents,
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None, "AGENTS.md must contain the routed sources-of-truth section"
    routed = set(re.findall(r"`(docs/[^ `]+\.md)`", section.group("body")))
    missing = sorted(path for path in routed if not (ROOT / path).is_file())
    assert missing == []
    untracked = sorted(path for path in routed if path not in TRACKED_PATHS)
    assert untracked == []
