"""Audit the finished public surface, local links, imports, input hashes and Git boundary."""

from pathlib import Path
import ast, hashlib, json, re, subprocess, importlib.util, sys, argparse

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = {
    ".gitignore",
    ".gitattributes",
    "README.md",
    "REPORT.md",
    "VALIDATION.md",
    "REVIEW.md",
    "REFACTOR_SUMMARY.md",
    "REFRACTOR_SUMMARY.md",
    "FINAL_PROJECT_STRUCTURE.md",
    "RESEARCH_HISTORY_SUMMARY.md",
    "CLEANUP_REPORT.md",
    "PRESENTATION_REFACTOR.md",
    "requirements.txt",
    "requirements-lock.txt",
    "pyproject.toml",
    "GARCH_RESEARCH_PLAN.md",
    "POST_CONVERGENCE_RESEARCH_SUMMARY.md",
    "FINAL_POST_CONVERGENCE_SUMMARY.md",
    "POST_CONVERGENCE_CLEANUP_REPORT.md",
    "FINAL_REPO_AUDIT.md",
    "MATH_RENDERING_FIX.md",
}
DIRECTORIES = {"src", "scripts", "tests", "results"}
DATA_FILES = {"README.md", "reference_inputs.json", "mainline_inputs.json"}


def files(root=ROOT):
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and (
            p.parent == root
            and p.name in TOP_FILES
            or p.relative_to(root).parts[0] in DIRECTORIES
            or p.parent == root / "data"
            and p.name in DATA_FILES
        )
    )


def audit(root=ROOT, index=False):
    paths = files(root)
    errors = []
    links = 0
    imports = []
    retired = []
    for p in paths:
        rel = p.relative_to(root).as_posix()
        if p.stat().st_size > 2_000_000:
            errors.append("Large public file: " + rel)
        if p.suffix.lower() in [".png", ".pdf"]:
            continue
        text = p.read_text(encoding="utf-8")
        if p.suffix == ".md":
            unsupported_math_macros = (
                r"\operatorname{",
                r"\DeclareMathOperator",
                r"\newcommand",
            )
            for line_number, line in enumerate(text.splitlines(), start=1):
                for macro in unsupported_math_macros:
                    if macro in line:
                        errors.append(
                            f"Unsupported math macro: {rel}:{line_number}: {macro}"
                        )
        for pattern in [
            r"[A-Za-z]:[\\/](?:Users|ProgramData)[\\/]",
            r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
            r"\b(?:PK|AK)[A-Z0-9]{18,25}\b",
            r"(?i)(?:api[_-]?key|api[_-]?secret|password)\s*[:=]\s*[\x22\x27][A-Za-z0-9+/]{12,}",
        ]:
            if re.search(pattern, text):
                errors.append("Private path or credential pattern: " + rel)
        if p.suffix == ".md":
            for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
                link = link.strip("<>")
                if link.startswith(("https://", "http://", "#")):
                    continue
                links += 1
                if not (p.parent / link.split("#")[0]).exists():
                    errors.append("Broken link: " + rel + " -> " + link)
        if p.suffix == ".py":
            tree = ast.parse(text, filename=rel)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level:
                    module = node.module or ""
                    target = p.parent.joinpath(*module.split(".")).with_suffix(".py")
                    if module and not target.exists():
                        errors.append(
                            "Missing relative import: " + rel + " -> " + module
                        )
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = (
                        [x.name for x in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module or ""]
                    )
                    imports.extend(dict(file=rel, module=n) for n in names)
            if p.name != "audit.py" and re.search(
                r"research/|research_archive_private|intraday_alpha_risk_lab|artifacts/(?:decision_layer|conditional_tail|equity_garch_full|treasury|dependence)",
                text,
            ):
                retired.append(rel)
    errors += ["Retired runtime reference: " + x for x in retired]
    if (root / "research").exists() and any((root / "research").rglob("*.py")):
        errors.append("Exploratory research code still public")
    ignored = None
    if (root / ".git").exists():
        probe = subprocess.run(
            ["git", "check-ignore", "-q", "research_archive_private/example.md"],
            cwd=root,
        )
        ignored = probe.returncode == 0
        if not ignored:
            errors.append("Private archive is not ignored")
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True
        ).stdout.splitlines()
        if any(
            x.startswith(("research_archive_private/", "data/local/", "artifacts/"))
            for x in tracked
        ):
            errors.append("Private data/archive tracked")
        if index:
            allowed = {p.relative_to(root).as_posix() for p in paths}
            errors += [
                "Staged nonpublic or deleted path: " + x
                for x in tracked
                if x not in allowed
            ]
            errors += [
                "Public file not staged: " + x for x in sorted(allowed - set(tracked))
            ]
    inputs = "NOT_PRESENT"
    if (root / "data/local/SPY.csv").exists():
        manifest = json.loads((root / "data/mainline_inputs.json").read_text())
        for name, h in manifest.items():
            p = root / "data/local" / name
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
                errors.append("Input fingerprint mismatch: " + name)
        inputs = "PASS" if not any("fingerprint" in e for e in errors) else "FAIL"
    return dict(
        status="PASS" if not errors else "FAIL",
        public_files=len(paths),
        public_bytes=sum(p.stat().st_size for p in paths),
        local_links_checked=links,
        broken_reference_count=sum("Broken link" in x for x in errors),
        private_archive_gitignored=ignored,
        input_hashes=inputs,
        retired_runtime_references=retired,
        imports=imports,
        errors=errors,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", action="store_true")
    args = parser.parse_args()
    result = audit(index=args.index)
    print(json.dumps({k: v for k, v in result.items() if k != "imports"}, indent=2))
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
