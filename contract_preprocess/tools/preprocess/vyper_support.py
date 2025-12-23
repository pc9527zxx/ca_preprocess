from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.request import urlopen

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version


_VYPER_STD_JSON: Dict[str, Any] = {
    "language": "Vyper",
    "sources": {},
    "settings": {
        "outputSelection": {
            "*": {
                "*": [
                    "abi",
                    "devdoc",
                    "userdoc",
                    "evm.bytecode",
                    "evm.deployedBytecode",
                    "evm.deployedBytecode.sourceMap",
                ],
                "": ["ast"],
            }
        }
    },
}


@dataclass(frozen=True)
class VyperFunction:
    name: str
    visibility: str  # external | internal
    calls: List[Dict[str, Any]]


def detect_vyper_version_spec(source: str) -> Optional[str]:
    """
    Best-effort detection of Vyper version spec from the first lines of a file.

    Supports:
      - '# @version 0.3.10'
      - '# @version ^0.2.0'
      - '# pragma version 0.3.10'
      - '# pragma version ^0.3.0'
    """
    header = source.splitlines()[:50]
    patterns = [
        r"^\s*#\s*@version\s+(?P<spec>[^#\s]+)\s*$",
        r"^\s*#\s*pragma\s+version\s+(?P<spec>[^#\s]+)\s*$",
    ]
    for line in header:
        for pat in patterns:
            m = re.match(pat, line, flags=re.IGNORECASE)
            if not m:
                continue
            spec = (m.group("spec") or "").strip()
            if spec.startswith("v"):
                spec = spec[1:]
            return spec or None
    return None


def _caret_to_specifier(spec: str) -> SpecifierSet:
    raw = spec.strip()
    assert raw.startswith("^")
    v = Version(raw[1:])
    lower = f">={v.public}"
    # SemVer-ish caret: bump major, but if major==0 bump minor.
    if v.major == 0:
        upper = f"<0.{v.minor + 1}.0"
    else:
        upper = f"<{v.major + 1}.0.0"
    return SpecifierSet(",".join([lower, upper]))


def _specifier_from_version_spec(spec: str) -> SpecifierSet:
    raw = spec.strip()
    if not raw:
        return SpecifierSet()
    if raw.startswith("^"):
        return _caret_to_specifier(raw)
    # Exact version
    try:
        Version(raw)
        return SpecifierSet(f"=={raw}")
    except InvalidVersion:
        pass
    # PEP440-ish specifiers (best effort)
    return SpecifierSet(raw)


def _fetch_pypi_versions(package: str, *, timeout_s: int = 10) -> List[Version]:
    with urlopen(f"https://pypi.org/pypi/{package}/json", timeout=timeout_s) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    versions: List[Version] = []
    for v in payload.get("releases", {}).keys():
        try:
            ver = Version(v)
        except InvalidVersion:
            continue
        # Skip pre/dev by default: for compiler selection, stable is preferable.
        if ver.is_prerelease or ver.is_devrelease:
            continue
        versions.append(ver)
    return sorted(set(versions))


def resolve_vyper_version(spec: Optional[str], *, allow_network: bool = True) -> Optional[str]:
    if not spec:
        return None
    try:
        wanted = _specifier_from_version_spec(spec)
    except Exception:
        return spec

    # If it's already pinned (==x.y.z), just return it.
    if str(wanted).startswith("=="):
        return str(wanted).replace("==", "", 1).strip()

    if not allow_network:
        return spec

    versions = _fetch_pypi_versions("vyper")
    best: Optional[Version] = None
    for v in versions:
        if v in wanted:
            best = v
    return best.public if best else spec


def ensure_vyper_binary(version: str, *, cache_dir: Path) -> Path:
    """
    Ensure a `vyper` executable for a given version exists.
    Implementation: a dedicated venv per version under cache_dir.
    """
    env_dir = cache_dir / "vyper" / version
    vyper_bin = env_dir / "bin" / "vyper"
    if vyper_bin.exists():
        return vyper_bin

    env_dir.parent.mkdir(parents=True, exist_ok=True)
    venv.EnvBuilder(with_pip=True, clear=False).create(env_dir)

    py = env_dir / "bin" / "python"
    res = subprocess.run(
        [str(py), "-m", "pip", "install", f"vyper=={version}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if res.returncode != 0:
        out = res.stdout.decode("utf-8", errors="replace")
        raise RuntimeError(f"pip install vyper=={version} failed:\n{out}")

    if not vyper_bin.exists():
        raise RuntimeError(f"vyper binary missing after install: {vyper_bin}")
    return vyper_bin


def _walk(node: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(node, dict):
        if "ast_type" in node:
            yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _format_attr_chain(expr: Any) -> str:
    if not isinstance(expr, dict):
        return str(expr)
    t = expr.get("ast_type")
    if t == "Name":
        return str(expr.get("id") or "")
    if t == "Attribute":
        base = _format_attr_chain(expr.get("value"))
        attr = expr.get("attr") or ""
        if base:
            return f"{base}.{attr}"
        return str(attr)
    if t == "Subscript":
        return f"{_format_attr_chain(expr.get('value'))}[...]"
    return str(t or "expr")


def _vyper_visibility_from_decorators(decorators: Sequence[Any]) -> str:
    for d in decorators:
        if not isinstance(d, dict):
            continue
        if d.get("ast_type") == "Name":
            name = str(d.get("id") or "")
            if name in ("external", "internal"):
                return name
    # Vyper requires explicit visibility; fallback to external for best-effort.
    return "external"


def _extract_function_defs(module_ast: Dict[str, Any]) -> List[Dict[str, Any]]:
    if module_ast.get("ast_type") != "Module":
        return []
    funcs: List[Dict[str, Any]] = []
    for node in module_ast.get("body") or []:
        if isinstance(node, dict) and node.get("ast_type") == "FunctionDef":
            funcs.append(node)
    return funcs


def compile_vyper_standard_json(
    source_path: Path,
    *,
    vyper_bin: Path,
    source_override: Optional[str] = None,
) -> Dict[str, Any]:
    source = source_override if source_override is not None else source_path.read_text(encoding="utf8")
    std = json.loads(json.dumps(_VYPER_STD_JSON))  # deep copy
    # Use a stable short key to avoid path normalization issues across vyper versions.
    key = source_path.name
    std["sources"][key] = {"content": source}

    proc = subprocess.run(
        [str(vyper_bin), "--standard-json"],
        input=json.dumps(std).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    try:
        artifacts = json.loads(out) if out else {}
    except json.JSONDecodeError:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"vyper did not return JSON.\nstdout:\n{out}\nstderr:\n{stderr}") from None

    diagnostics = artifacts.get("errors") or []
    errors: List[str] = []
    for diag in diagnostics:
        if diag.get("severity") == "warning":
            continue
        errors.append(diag.get("formattedMessage") or diag.get("message") or str(diag))
    if errors:
        raise RuntimeError("\n\n".join(errors))
    return artifacts


def rewrite_vyper_version_directive(source: str, compiler_version: str) -> str:
    """
    Rewrite the first Vyper version directive in the header to match the selected compiler.
    This avoids hard failures when the source pins a version that can't be installed on the
    current Python runtime.
    """
    lines = source.splitlines()
    patterns = [
        r"^(\s*#\s*)@version\s+[^#\s]+\s*$",
        r"^(\s*#\s*)pragma\s+version\s+[^#\s]+\s*$",
    ]
    for i in range(min(len(lines), 50)):
        ln = lines[i]
        for pat in patterns:
            m = re.match(pat, ln, flags=re.IGNORECASE)
            if not m:
                continue
            prefix = m.group(1) or "# "
            lines[i] = f"{prefix}@version {compiler_version}"
            return "\n".join(lines) + ("\n" if source.endswith("\n") else "")
    return source


def extract_vyper_functions_and_calls(
    artifacts: Dict[str, Any],
    *,
    contract_name: str,
    include_external_calls: bool = True,
    include_solidity_calls: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns grouped functions: visibility -> list[function_entry]
    """
    # Vyper std-json uses the same key we provided (source_path.name)
    sources = artifacts.get("sources") or {}
    if not sources:
        return {k: [] for k in ["external", "public", "internal", "private"]}

    # Pick the first module AST we find.
    module_ast: Optional[Dict[str, Any]] = None
    for _k, v in sources.items():
        if isinstance(v, dict) and isinstance(v.get("ast"), dict):
            module_ast = v["ast"]
            break
    if module_ast is None:
        return {k: [] for k in ["external", "public", "internal", "private"]}

    func_defs = _extract_function_defs(module_ast)

    # Map name -> visibility for internal target resolution
    known: Dict[str, str] = {}
    for f in func_defs:
        name = str(f.get("name") or "")
        decorators = f.get("decorator_list") or []
        vis = _vyper_visibility_from_decorators(decorators if isinstance(decorators, list) else [])
        if name:
            known[name] = vis

    groups: Dict[str, List[Dict[str, Any]]] = {k: [] for k in ["external", "public", "internal", "private"]}

    for f in func_defs:
        name = str(f.get("name") or "")
        decorators = f.get("decorator_list") or []
        visibility = _vyper_visibility_from_decorators(decorators if isinstance(decorators, list) else [])
        fn_id = f"{contract_name}::{name}"

        seen: Set[Tuple[str, str, str]] = set()
        calls: List[Dict[str, Any]] = []

        for node in _walk(f.get("body") or []):
            if node.get("ast_type") != "Call":
                continue
            func_expr = node.get("func")
            if not isinstance(func_expr, dict):
                continue
            func_type = func_expr.get("ast_type")
            if func_type == "Attribute":
                value = func_expr.get("value")
                attr = str(func_expr.get("attr") or "")
                if isinstance(value, dict) and value.get("ast_type") == "Name" and value.get("id") == "self":
                    # Internal call: self.foo(...)
                    callee = attr
                    callee_id = f"{contract_name}::{callee}"
                    key = ("internal", "function", callee_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    calls.append(
                        {
                            "kind": "function",
                            "edge": "internal",
                            "id": callee_id,
                            "name": callee,
                            "display": f"{contract_name}.{callee}",
                            "visibility": known.get(callee),
                            "contract_context": contract_name,
                            "declared_in": contract_name,
                        }
                    )
                elif include_external_calls:
                    display = _format_attr_chain(func_expr)
                    key = ("external", "unknown", display)
                    if key in seen:
                        continue
                    seen.add(key)
                    calls.append({"kind": "unknown", "edge": "external", "display": display})
            elif func_type == "Name":
                if not include_solidity_calls:
                    continue
                builtin = str(func_expr.get("id") or "")
                key = ("solidity", "solidity", builtin)
                if key in seen:
                    continue
                seen.add(key)
                calls.append({"kind": "solidity", "edge": "solidity", "name": builtin})

        calls.sort(key=lambda c: (c.get("edge") or "", c.get("kind") or "", c.get("display") or c.get("name") or ""))

        fn_entry: Dict[str, Any] = {
            "kind": "function",
            "id": fn_id,
            "name": name,
            "display": f"{contract_name}.{name}",
            "visibility": visibility,
            "contract_context": contract_name,
            "declared_in": contract_name,
            "is_constructor": False,
            "is_fallback": name == "__default__",
            "is_receive": False,
            "is_shadowed": False,
            "calls": calls,
        }
        groups.setdefault(visibility, []).append(fn_entry)

    for v in groups:
        groups[v].sort(key=lambda fn: (fn.get("display") or "", fn.get("id") or ""))

    return groups


def extract_vyper_functions_and_calls_from_source(
    source: str,
    *,
    contract_name: str,
    include_external_calls: bool = True,
    include_solidity_calls: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fallback extraction that does not require compilation.
    Best-effort: identifies top-level function defs and `self.<fn>(...)` call edges.
    """

    def strip_comment(line: str) -> str:
        if "#" in line:
            return line.split("#", 1)[0]
        return line

    def indent_width(line: str) -> int:
        # tabs are rare in Vyper sources, but handle them deterministically.
        return len(line.expandtabs(4)) - len(line.lstrip(" \t").expandtabs(4))

    lines = source.splitlines()
    functions: List[Tuple[str, str, List[str]]] = []  # (name, visibility, body_lines)
    decorators: List[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s or s.startswith("#"):
            i += 1
            continue
        if s.startswith("@"):
            decorators.append(s)
            i += 1
            continue

        m = re.match(r"^(?P<indent>[ \t]*)def\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(", raw)
        if not m:
            decorators = []
            i += 1
            continue

        fn_indent = indent_width(m.group("indent") or "")
        name = m.group("name")
        visibility = "external"
        if any(d.startswith("@internal") for d in decorators):
            visibility = "internal"
        elif any(d.startswith("@external") for d in decorators):
            visibility = "external"

        decorators = []
        i += 1
        body: List[str] = []
        while i < len(lines):
            ln = lines[i]
            if not ln.strip():
                body.append(ln)
                i += 1
                continue
            if indent_width(ln) <= fn_indent:
                break
            body.append(ln)
            i += 1
        functions.append((name, visibility, body))

    known_vis = {name: vis for name, vis, _ in functions}
    groups: Dict[str, List[Dict[str, Any]]] = {k: [] for k in ["external", "public", "internal", "private"]}

    internal_call_re = re.compile(r"\bself\.(?P<fn>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
    external_attr_call_re = re.compile(
        r"\b(?P<obj>[A-Za-z_][A-Za-z0-9_]*)\.(?P<fn>[A-Za-z_][A-Za-z0-9_]*)\s*\("
    )

    for name, visibility, body_lines in functions:
        fn_id = f"{contract_name}::{name}"
        seen: Set[Tuple[str, str, str]] = set()
        calls: List[Dict[str, Any]] = []

        for ln in body_lines:
            code = strip_comment(ln)
            for m in internal_call_re.finditer(code):
                callee = m.group("fn")
                callee_id = f"{contract_name}::{callee}"
                key = ("internal", "function", callee_id)
                if key in seen:
                    continue
                seen.add(key)
                calls.append(
                    {
                        "kind": "function",
                        "edge": "internal",
                        "id": callee_id,
                        "name": callee,
                        "display": f"{contract_name}.{callee}",
                        "visibility": known_vis.get(callee),
                        "contract_context": contract_name,
                        "declared_in": contract_name,
                    }
                )

            if include_external_calls:
                for m in external_attr_call_re.finditer(code):
                    if m.group("obj") == "self":
                        continue
                    display = f"{m.group('obj')}.{m.group('fn')}"
                    key = ("external", "unknown", display)
                    if key in seen:
                        continue
                    seen.add(key)
                    calls.append({"kind": "unknown", "edge": "external", "display": display})

            if include_solidity_calls:
                # Vyper has Python-like builtins; treat bare calls as leafs.
                bare = re.findall(r"\\b([A-Za-z_][A-Za-z0-9_]*)\\s*\\(", code)
                for b in bare:
                    if b in ("def", "self"):
                        continue
                    key = ("solidity", "solidity", b)
                    if key in seen:
                        continue
                    seen.add(key)
                    calls.append({"kind": "solidity", "edge": "solidity", "name": b})

        calls.sort(key=lambda c: (c.get("edge") or "", c.get("kind") or "", c.get("display") or c.get("name") or ""))
        fn_entry: Dict[str, Any] = {
            "kind": "function",
            "id": fn_id,
            "name": name,
            "display": f"{contract_name}.{name}",
            "visibility": visibility,
            "contract_context": contract_name,
            "declared_in": contract_name,
            "is_constructor": False,
            "is_fallback": name == "__default__",
            "is_receive": False,
            "is_shadowed": False,
            "calls": calls,
        }
        groups.setdefault(visibility, []).append(fn_entry)

    for v in groups:
        groups[v].sort(key=lambda fn: (fn.get("display") or "", fn.get("id") or ""))

    return groups


def preprocess_vyper_file(
    source_path: Path,
    *,
    vyper_version: Optional[str],
    cache_dir: Optional[Path] = None,
    allow_network: bool = True,
    auto_install: bool = True,
    include_external_calls: bool = True,
    include_solidity_calls: bool = False,
) -> Dict[str, Any]:
    source = source_path.read_text(encoding="utf8")
    spec = vyper_version or detect_vyper_version_spec(source)
    resolved = resolve_vyper_version(spec, allow_network=allow_network)

    def best_effort_vyper_versions() -> List[str]:
        candidates: List[str] = []

        if resolved:
            try:
                candidates.append(Version(resolved).public)
            except InvalidVersion:
                pass

        # If the source pins an older version that can't be installed on the current Python,
        # try the newest patch versions in the same minor series (e.g. 0.3.x).
        if allow_network and spec:
            try:
                pinned = Version(str(spec).lstrip("^v"))
                same_minor = [
                    v for v in _fetch_pypi_versions("vyper") if (v.major, v.minor) == (pinned.major, pinned.minor)
                ]
                # Try newest first; limit to keep it fast.
                for v in reversed(same_minor[-10:]):
                    if v.public not in candidates:
                        candidates.append(v.public)
            except Exception:
                pass

        return candidates

    cache_root = cache_dir or Path(os.environ.get("CONTRACT_PREPROCESS_CACHE", Path.home() / ".cache")) / "contract-preprocess"

    artifacts: Optional[Dict[str, Any]] = None
    used_version: Optional[str] = None
    compile_error: Optional[Exception] = None

    if auto_install:
        last_error: Optional[Exception] = None
        for v in best_effort_vyper_versions():
            try:
                vyper_bin = ensure_vyper_binary(v, cache_dir=cache_root)
                patched_source = rewrite_vyper_version_directive(source, v)
                artifacts = compile_vyper_standard_json(
                    source_path, vyper_bin=vyper_bin, source_override=patched_source
                )
                used_version = v
                break
            except Exception as e:  # pylint: disable=broad-except
                last_error = e
                continue

        if artifacts is None and last_error is not None and not allow_network:
            raise last_error

    if artifacts is None:
        # Try to find a sibling 'vyper' next to the running python as a fallback.
        candidate = Path(sys.executable).with_name("vyper")
        vyper_bin = candidate if candidate.exists() else Path("vyper")
        try:
            artifacts = compile_vyper_standard_json(source_path, vyper_bin=vyper_bin, source_override=source)
        except Exception as e:  # pylint: disable=broad-except
            compile_error = e

    # Best-effort contract name: file stem.
    contract_name = source_path.stem

    if artifacts is None:
        functions = extract_vyper_functions_and_calls_from_source(
            source,
            contract_name=contract_name,
            include_external_calls=include_external_calls,
            include_solidity_calls=include_solidity_calls,
        )
        return {
            "contract_name": contract_name,
            "compiler": {"name": "vyper", "version": used_version or (resolved or spec), "mode": "source"},
            "functions": functions,
            "warning": str(compile_error) if compile_error else "vyper compilation failed; used source parser",
        }

    # Prefer std-json contracts key when available.
    contracts = artifacts.get("contracts") or {}
    if contracts:
        # contracts: {source_key: {ContractName: {...}}}
        first_src = next(iter(contracts.values()), {})
        if isinstance(first_src, dict) and first_src:
            contract_name = next(iter(first_src.keys()))

    functions = extract_vyper_functions_and_calls(
        artifacts,
        contract_name=contract_name,
        include_external_calls=include_external_calls,
        include_solidity_calls=include_solidity_calls,
    )

    return {
        "contract_name": contract_name,
        "compiler": {"name": "vyper", "version": used_version or (resolved or spec)},
        "functions": functions,
    }
