from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version
from solc_select.solc_select import artifact_path, install_artifacts, installed_versions


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "SourceCode"
RESULTS_DIR = ROOT / "Results"


def _strip_solidity_comments(text: str) -> str:
    # Remove /* */ then // comments (best effort; not a full lexer).
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    return text


def _iter_addresses() -> List[str]:
    addrs: List[str] = []
    for p in SOURCE_DIR.iterdir():
        if not p.is_dir():
            continue
        name = p.name.lower()
        if re.fullmatch(r"0x[0-9a-f]{40}", name):
            addrs.append(name)
    return sorted(addrs)


def _resolve_addr_dir(addr: str) -> Optional[Path]:
    """
    Resolve an address directory under SOURCE_DIR case-insensitively.
    Some datasets may store EIP-55 checksummed directory names.
    """
    direct = SOURCE_DIR / addr
    if direct.is_dir():
        return direct
    want = addr.lower()
    for p in SOURCE_DIR.iterdir():
        if p.is_dir() and p.name.lower() == want:
            return p
    return None


def _detect_vyper_file(addr_dir: Path) -> Optional[Path]:
    # Prefer .vy in the directory root.
    for p in sorted(addr_dir.glob("*.vy")):
        return p

    # Fallback: sometimes Vyper source is saved as .sol
    for p in sorted(addr_dir.glob("*.sol")):
        head = p.read_text(encoding="utf8", errors="ignore").splitlines()[:30]
        if any(re.match(r"^\s*#\s*(@version|pragma\s+version)\b", ln) for ln in head):
            return p
    return None


def _iter_project_solidity_files(addr_dir: Path) -> List[Path]:
    files: List[Path] = []
    for p in addr_dir.rglob("*.sol"):
        if any(part.startswith("@") for part in p.parts):
            continue
        try:
            head = p.read_text(encoding="utf8", errors="ignore").splitlines()[:60]
        except Exception:
            continue
        if any("pragma solidity" in ln for ln in head):
            files.append(p)
    return sorted(files)


def _parse_solidity_imports(text: str) -> List[str]:
    # Handles: import "x"; import {A} from "x"; import * as X from "x";
    # Not a full parser; good enough for repo-root detection.
    no_comments = _strip_solidity_comments(text)
    return re.findall(r"\bimport\b[^;]*?[\"']([^\"']+)[\"']\s*;", no_comments)


def _build_remap_map(addr_dir: Path) -> Dict[str, Path]:
    remaps: Dict[str, Path] = {}
    for child in sorted(addr_dir.iterdir()):
        if child.is_dir() and child.name.startswith("@"):
            remaps[f"{child.name}/"] = child.resolve()
    return remaps


def _resolve_import(addr_dir: Path, current_file: Path, imp: str, remaps: Dict[str, Path]) -> Optional[Path]:
    if imp.startswith("@"):
        for prefix, base in remaps.items():
            if imp.startswith(prefix):
                rel = imp[len(prefix) :]
                candidate = (base / rel).resolve()
                if candidate.exists():
                    return candidate
        return None

    # Relative imports
    candidate = (current_file.parent / imp).resolve()
    if candidate.exists():
        return candidate

    # Some repos use imports relative to the address directory root.
    candidate = (addr_dir / imp).resolve()
    if candidate.exists():
        return candidate

    return None


def _collect_import_closure(addr_dir: Path, root: Path) -> Set[Path]:
    remaps = _build_remap_map(addr_dir)
    visited: Set[Path] = set()
    stack: List[Path] = [root.resolve()]

    while stack:
        p = stack.pop()
        if p in visited or not p.exists() or p.suffix != ".sol":
            continue
        visited.add(p)

        try:
            txt = p.read_text(encoding="utf8", errors="ignore")
        except Exception:
            continue

        for imp in _parse_solidity_imports(txt):
            resolved = _resolve_import(addr_dir, p, imp, remaps)
            if resolved is not None and resolved not in visited:
                stack.append(resolved)

    return visited


def _pick_solidity_root(addr_dir: Path, files: Sequence[Path]) -> Optional[Path]:
    if not files:
        return None

    imported: Set[Path] = set()
    for f in files:
        try:
            txt = f.read_text(encoding="utf8", errors="ignore")
        except Exception:
            continue
        for imp in _parse_solidity_imports(txt):
            if imp.startswith("@"):
                continue
            if imp.startswith("http://") or imp.startswith("https://"):
                continue
            resolved = (f.parent / imp).resolve()
            if resolved.exists() and resolved.suffix == ".sol":
                imported.add(resolved)

    roots = [p for p in files if p.resolve() not in imported]
    candidates = roots if roots else list(files)

    best: Optional[Tuple[float, Path]] = None
    for p in candidates:
        try:
            txt = p.read_text(encoding="utf8", errors="ignore")
        except Exception:
            continue
        stripped = _strip_solidity_comments(txt)
        # Heuristic: prefer files that declare contracts and import others.
        n_contract = len(re.findall(r"\bcontract\s+\w+", stripped))
        n_library = len(re.findall(r"\blibrary\s+\w+", stripped))
        n_import = len(re.findall(r"\bimport\b", stripped))
        score = (n_contract * 10.0) + (n_library * 3.0) + (n_import * 1.0) - (p.as_posix().count("/") * 0.1)
        if best is None or score > best[0]:
            best = (score, p)
    return best[1] if best else candidates[0]


def _solidity_pragma_spec(text: str) -> Optional[str]:
    no_comments = _strip_solidity_comments(text)
    m = re.search(r"\bpragma\s+solidity\s+([^;]+);", no_comments)
    if not m:
        return None
    return m.group(1).strip()


def _caret_to_specifier(v: Version) -> SpecifierSet:
    lower = f">={v.public}"
    if v.major == 0:
        # 0.y.z -> <0.(y+1).0
        upper = f"<0.{v.minor + 1}.0"
    else:
        upper = f"<{v.major + 1}.0.0"
    return SpecifierSet(",".join([lower, upper]))


def _specifier_from_solidity_pragma(spec: str) -> SpecifierSet:
    raw = spec.strip()
    if not raw:
        return SpecifierSet()
    # Solidity allows multiple ranges separated by spaces.
    parts = [p for p in re.split(r"\s+", raw) if p]
    converted: List[str] = []
    for p in parts:
        p = p.strip()
        if p.startswith("^"):
            v = Version(p[1:])
            caret = _caret_to_specifier(v)
            converted.append(str(caret))
        elif re.match(r"^\d+\.\d+\.\d+$", p):
            converted.append(f"=={p}")
        else:
            converted.append(p)
    # SpecifierSet expects comma-separated.
    return SpecifierSet(",".join(converted))


def _select_solc_version_for_files(files: Iterable[Path]) -> Optional[str]:
    wanted_sets: List[SpecifierSet] = []
    exact_versions: Set[str] = set()

    for f in files:
        try:
            txt = f.read_text(encoding="utf8", errors="ignore")
        except Exception:
            continue
        pragma = _solidity_pragma_spec(txt)
        if not pragma:
            continue
        pragma = pragma.strip()
        if re.fullmatch(r"\d+\.\d+\.\d+", pragma):
            exact_versions.add(pragma)
        try:
            wanted_sets.append(_specifier_from_solidity_pragma(pragma))
        except Exception:
            continue

    # If any file pins an exact version, prefer it (must be consistent to compile).
    if len(exact_versions) == 1:
        return next(iter(exact_versions))

    # Prefer already-installed versions for speed.
    installed: List[Version] = []
    for v in installed_versions():
        try:
            installed.append(Version(v))
        except InvalidVersion:
            continue
    installed = sorted(set(installed))

    best: Optional[Version] = None
    for v in installed:
        if all(v in s for s in wanted_sets):
            best = v
    return best.public if best is not None else None


def _ensure_solc(version: str) -> Path:
    if version not in installed_versions():
        ok = install_artifacts([version])
        if not ok:
            raise RuntimeError(f"solc-select could not install {version}")
    return artifact_path(version)


def _solc_remaps(addr_dir: Path) -> Optional[str]:
    remaps: List[str] = []
    for child in sorted(addr_dir.iterdir()):
        if child.is_dir() and child.name.startswith("@"):
            remaps.append(f"{child.name}/={os.path.relpath(child, Path.cwd())}/")
    return " ".join(remaps) if remaps else None


def _run(cmd: List[str], log_path: Path, *, env: Optional[Dict[str, str]] = None) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf8") as log:
        log.write("CMD: " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.run(
            cmd,
            stdout=log,
            stderr=log,
            env=env or os.environ.copy(),
            check=False,
        )
    return proc.returncode


def _result_has_errors(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf8"))
    except Exception:
        return True
    return bool(data.get("errors"))


def process_address(addr: str) -> Tuple[bool, str]:
    addr_dir = _resolve_addr_dir(addr)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = RESULTS_DIR / f"{addr}.json"
    out_log = RESULTS_DIR / f"{addr}.log"
    out_external = RESULTS_DIR / f"{addr}_external"
    out_json_arg = os.path.relpath(out_json, Path.cwd())
    out_external_arg = os.path.relpath(out_external, Path.cwd())
    if out_external.exists():
        shutil.rmtree(out_external, ignore_errors=True)

    if addr_dir is None or not addr_dir.is_dir():
        out_json.write_text(
            json.dumps(
                {
                    "tool": "contract-preprocess",
                    "targets": [addr],
                    "compilations": [],
                    "errors": [{"target": addr, "stage": "sourcecode", "error": "no source directory under Etherscan/SourceCode"}],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf8",
        )
        out_log.write_text("SKIP: no source directory\n", encoding="utf8")
        return False, "no-source-dir"

    vyper_file = _detect_vyper_file(addr_dir)
    if vyper_file is not None:
        cmd = [
            sys.executable,
            "-m",
            "contract_preprocess.tools.preprocess",
            "--no-fail",
            "--emit-callgraph",
            "--dump-external-dir",
            out_external_arg,
            "-o",
            out_json_arg,
            os.path.relpath(vyper_file, Path.cwd()),
        ]
        _run(cmd, out_log)
        return not _result_has_errors(out_json), "vyper"

    sol_files = _iter_project_solidity_files(addr_dir)
    root = _pick_solidity_root(addr_dir, sol_files)
    if root is None:
        out_json.write_text(
            json.dumps(
                {
                    "tool": "contract-preprocess",
                    "targets": [addr],
                    "compilations": [],
                    "errors": [{"target": addr, "stage": "sourcecode", "error": "no Solidity/Vyper sources found"}],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf8",
        )
        out_log.write_text("SKIP: no sources found\n", encoding="utf8")
        return False, "no-sources"

    closure = _collect_import_closure(addr_dir, root)
    solc_ver = _select_solc_version_for_files(closure) or _select_solc_version_for_files(sol_files) or "0.8.24"
    solc_bin = _ensure_solc(solc_ver)
    remaps = _solc_remaps(addr_dir)

    cmd = [
        sys.executable,
        "-m",
        "contract_preprocess.tools.preprocess",
        "--no-fail",
        "--emit-callgraph",
        "--dump-external-dir",
        out_external_arg,
        "--compile-force-framework",
        "solc",
        "--solc",
        os.path.relpath(solc_bin, Path.cwd()) if str(solc_bin).startswith(str(Path.cwd())) else str(solc_bin),
        "-o",
        out_json_arg,
    ]
    if remaps:
        cmd += ["--solc-remaps", remaps]
    cmd.append(os.path.relpath(root, Path.cwd()))

    _run(cmd, out_log)
    return not _result_has_errors(out_json), f"solc:{solc_ver}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process locally-saved verified sources under Etherscan/SourceCode/<address> and write outputs to Etherscan/Results/.",
        usage="python Etherscan/run_all.py [0xADDR ...]",
    )
    parser.add_argument(
        "addresses",
        nargs="*",
        help="Contract address(es) to process (0x...). If omitted, processes all folders under Etherscan/SourceCode/.",
    )
    args = parser.parse_args()

    addrs: List[str]
    if args.addresses:
        addrs = []
        for a in args.addresses:
            a = a.strip().lower()
            if not re.fullmatch(r"0x[0-9a-f]{40}", a):
                raise SystemExit(f"Invalid address: {a}")
            addrs.append(a)
    else:
        addrs = _iter_addresses()
    ok = 0
    for addr in addrs:
        success, tag = process_address(addr)
        status = "OK" if success else "FAIL"
        print(f"{status}\t{addr}\t{tag}")
        ok += 1 if success else 0
    print(f"done: {ok}/{len(addrs)} succeeded")


if __name__ == "__main__":
    main()
