import argparse
import glob
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from crytic_compile import CryticCompile, compile_all, cryticparser, is_supported
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version
from solc_select.solc_select import artifact_path, get_available_versions, install_artifacts, installed_versions

from contract_preprocess import ContractPreprocess
from contract_preprocess.tools.preprocess.function_call_tree import (
    build_function_call_edges,
    contract_functions_by_visibility,
)
from contract_preprocess.tools.preprocess.vyper_support import preprocess_vyper_file

logging.basicConfig()
logger = logging.getLogger("contract-preprocess")
logger.setLevel(logging.INFO)


def _safe_fs_name(value: str) -> str:
    cleaned = value.replace("::", "__")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    cleaned = cleaned.strip("._-")
    return cleaned or "unnamed"


def _write_callgraph_dot(compilation: Dict[str, Any], dot_path: Path) -> None:
    """
    Write a dot callgraph for a single compilation entry from the tool JSON.
    Includes function->(function/unknown/variable/solidity) edges; edge labels are preserved
    (internal/external/library/modifier/base-constructor/solidity).
    """
    nodes: Dict[str, Tuple[str, str]] = {}
    edges: Set[Tuple[str, str, str]] = set()

    for contract in compilation.get("contracts", []):
        for visibility, functions in (contract.get("functions") or {}).items():
            for fn in functions:
                if fn.get("kind") != "function":
                    continue
                fn_id = fn.get("id")
                if not fn_id:
                    continue
                label = fn.get("display") or fn.get("name") or fn_id
                if visibility:
                    label = f"{label}\\n[{visibility}]"
                nodes[str(fn_id)] = (str(label), "box")

                for call in fn.get("calls") or []:
                    kind = call.get("kind") or "unknown"
                    if kind == "function":
                        dst = call.get("id")
                        if not dst:
                            continue
                        dst_id = str(dst)
                        dst_label = str(call.get("display") or call.get("name") or dst_id)
                        nodes.setdefault(dst_id, (dst_label, "box"))
                    else:
                        dst_label = str(call.get("display") or call.get("name") or kind)
                        dst_id = f"{kind}::{dst_label}"
                        shape = "ellipse" if kind in ("unknown", "variable") else "diamond"
                        nodes.setdefault(dst_id, (dst_label, shape))
                    edges.add((str(fn_id), str(dst_id), str(call.get("edge") or "")))

    def esc(s: str) -> str:
        return s.replace("\\\\", "\\\\\\\\").replace('"', '\\"')

    def edge_attrs(edge_kind: str) -> str:
        color = {
            "internal": "black",
            "external": "red",
            "library": "blue",
            "modifier": "gray40",
            "base-constructor": "purple4",
            "solidity": "darkorange3",
        }.get(edge_kind, "black")
        label = edge_kind or ""
        return f' [label="{esc(label)}", color="{color}"]'

    dot_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        'digraph "callgraph" {',
        "  rankdir=LR;",
        "  node [fontsize=10];",
    ]
    for node_id, (label, shape) in sorted(nodes.items(), key=lambda kv: kv[0]):
        lines.append(f'  "{esc(node_id)}" [label="{esc(label)}", shape="{esc(shape)}"];')
    for src, dst, kind in sorted(edges, key=lambda e: (e[0], e[1], e[2])):
        lines.append(f'  "{esc(src)}" -> "{esc(dst)}"{edge_attrs(kind)};')
    lines.append("}")
    dot_path.write_text("\n".join(lines) + "\n", encoding="utf8")

    # Best-effort render to SVG if graphviz is available.
    svg_path = dot_path.with_suffix(".svg")
    try:
        import subprocess  # pylint: disable=import-outside-toplevel

        subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)], check=False)
    except Exception:  # pylint: disable=broad-except
        pass


def _source_hint(obj: Any) -> Optional[str]:
    sm = getattr(obj, "source_mapping", None)
    if sm is None:
        return None
    try:
        fn = getattr(getattr(sm, "filename", None), "relative", None) or getattr(
            getattr(sm, "filename", None), "absolute", None
        )
        lines = getattr(sm, "lines", None) or []
        if fn and lines:
            return f"{fn}:{lines[0]}-{lines[-1]}"
        return str(fn) if fn else None
    except Exception:  # pylint: disable=broad-except
        return None


def _source_extension(obj: Any, default: str = ".sol") -> str:
    sm = getattr(obj, "source_mapping", None)
    if sm is None:
        return default
    try:
        abs_path = getattr(getattr(sm, "filename", None), "absolute", None)
        if abs_path:
            suffix = Path(str(abs_path)).suffix
            return suffix if suffix else default
    except Exception:  # pylint: disable=broad-except
        return default
    return default


def _source_content(obj: Any) -> Optional[str]:
    sm = getattr(obj, "source_mapping", None)
    if sm is None:
        return None
    try:
        content = getattr(sm, "content", None)
        return str(content) if content is not None else None
    except Exception:  # pylint: disable=broad-except
        return None


def _dump_external_function_bundle(
    fn: Any,
    out_dir: Path,
    *,
    include_external_calls: bool,
    include_library_calls: bool,
    include_solidity_calls: bool,
    include_modifiers: bool,
    include_base_constructors: bool,
) -> Optional[Path]:
    """
    Write a single file for an external function containing:
      - the external function source snippet
      - source snippets for its *direct* callee functions (no recursion)
    """
    from contract_preprocess.tools.preprocess.function_call_tree import (
        function_display_name,
        function_uid,
        iter_call_targets,
    )

    def should_keep_edge(edge: str) -> bool:
        if edge == "external":
            return include_external_calls
        if edge == "library":
            return include_library_calls
        if edge == "solidity":
            return include_solidity_calls
        if edge == "modifier":
            return include_modifiers
        if edge == "base-constructor":
            return include_base_constructors
        return True

    contract_ctx = getattr(fn, "contract", None)
    contract_name = getattr(contract_ctx, "name", None) or getattr(
        getattr(fn, "contract_declarer", None), "name", None
    )
    contract_name = str(contract_name) if contract_name else "UnknownContract"

    fn_id = function_uid(fn)
    ext = _source_extension(fn, default=".sol")
    rel_contract_dir = Path(_safe_fs_name(contract_name))
    out_path = out_dir / rel_contract_dir / f"{_safe_fs_name(fn_id)}{ext}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sections: List[str] = []
    sections.append(f"// entry (external): {function_display_name(fn)}")
    src_hint = _source_hint(fn)
    if src_hint:
        sections.append(f"// source: {src_hint}")
    content = _source_content(fn)
    if content:
        sections.append(content.strip("\n"))
    else:
        sections.append("// <no source mapping available>")

    # Collect all *reachable* functions (transitive, no recursion output), plus leaf call targets.
    seen: Set[str] = {fn_id}
    reachable: List[Tuple[str, Any]] = []
    leaf_targets: Set[Tuple[str, str, str]] = set()

    pending: List[Any] = [fn]
    while pending:
        cur = pending.pop()
        fn_targets: List[Tuple[str, str, Any]] = []
        leafs: List[Tuple[str, str, str]] = []
        for call in iter_call_targets(cur):
            if not should_keep_edge(call.edge):
                continue
            if call.kind == "function":
                callee = getattr(call, "target", None)
                if callee is None:
                    leafs.append((call.edge, "unknown", str(call.label)))
                    continue
                if not getattr(callee, "is_implemented", True):
                    # Interface/abstract: keep as a leaf label but don't dump code.
                    leafs.append((call.edge, "abstract", function_display_name(callee)))
                    continue
                try:
                    callee_id = function_uid(callee)
                except Exception:  # pylint: disable=broad-except
                    leafs.append((call.edge, "unknown", str(call.label)))
                    continue
                fn_targets.append((call.edge, callee_id, callee))
            elif call.kind in ("variable", "solidity", "unknown"):
                leafs.append((call.edge, call.kind, str(call.label)))
            else:
                leafs.append((call.edge, "unknown", str(call.label)))

        # Deterministic traversal for stable output.
        leafs.sort(key=lambda t: (t[0], t[1], t[2]))
        for edge, kind, label in leafs:
            leaf_targets.add((edge, kind, label))

        fn_targets.sort(key=lambda t: (t[0], t[1]))
        for edge, callee_id, callee in fn_targets:
            if callee_id in seen:
                continue
            seen.add(callee_id)
            reachable.append((edge, callee))
            pending.append(callee)

    if leaf_targets:
        sections.append("")
        sections.append("// leaf targets (no body):")
        for edge, kind, label in sorted(leaf_targets, key=lambda t: (t[0], t[1], t[2])):
            sections.append(f"//   - ({edge}) [{kind}]: {label}")

    for edge, callee in reachable:
        sections.append("")
        vis = getattr(callee, "visibility", None)
        vis_s = f"{vis}" if vis else "unknown"
        sections.append(f"// ---- reachable ({edge}) [{vis_s}]: {function_display_name(callee)}")
        callee_hint = _source_hint(callee)
        if callee_hint:
            sections.append(f"// source: {callee_hint}")
        callee_content = _source_content(callee)
        if callee_content:
            sections.append(callee_content.strip("\n"))
        else:
            sections.append("// <no source mapping available>")

    out_path.write_text("\n".join(sections).rstrip() + "\n", encoding="utf8")
    return out_path


def _strip_solidity_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    return text


def _solidity_imports(text: str) -> List[str]:
    no_comments = _strip_solidity_comments(text)
    return re.findall(r"\bimport\b[^;]*?[\"']([^\"']+)[\"']\s*;", no_comments)


def _collect_solidity_closure(root: Path) -> List[Path]:
    visited: Set[Path] = set()
    stack: List[Path] = [root.resolve()]
    while stack:
        p = stack.pop()
        if p in visited or not p.exists() or p.suffix != ".sol":
            continue
        visited.add(p)
        try:
            txt = p.read_text(encoding="utf8", errors="ignore")
        except Exception:  # pylint: disable=broad-except
            continue
        for imp in _solidity_imports(txt):
            if imp.startswith("@") or imp.startswith("http://") or imp.startswith("https://"):
                continue
            candidate = (p.parent / imp).resolve()
            if candidate.exists() and candidate.suffix == ".sol":
                stack.append(candidate)
    return sorted(visited)


def _solidity_pragma_spec(text: str) -> Optional[str]:
    no_comments = _strip_solidity_comments(text)
    m = re.search(r"\bpragma\s+solidity\s+([^;]+);", no_comments)
    return m.group(1).strip() if m else None


def _caret_to_specifier(v: Version) -> SpecifierSet:
    lower = f">={v.public}"
    if v.major == 0:
        upper = f"<0.{v.minor + 1}.0"
    else:
        upper = f"<{v.major + 1}.0.0"
    return SpecifierSet(",".join([lower, upper]))


def _specifier_from_solidity_pragma(spec: str) -> SpecifierSet:
    raw = spec.strip()
    if not raw:
        return SpecifierSet()
    parts = [p for p in re.split(r"\s+", raw) if p]
    converted: List[str] = []
    for p in parts:
        if p.startswith("^"):
            converted.append(str(_caret_to_specifier(Version(p[1:]))))
        elif re.match(r"^\d+\.\d+\.\d+$", p):
            converted.append(f"=={p}")
        else:
            converted.append(p)
    return SpecifierSet(",".join(converted))


def _pick_solc_version_for_files(files: List[Path]) -> Optional[str]:
    wanted_sets: List[SpecifierSet] = []
    exact_versions: Set[str] = set()

    for f in files:
        try:
            txt = f.read_text(encoding="utf8", errors="ignore")
        except Exception:  # pylint: disable=broad-except
            continue
        pragma = _solidity_pragma_spec(txt)
        if not pragma:
            continue
        if re.fullmatch(r"\d+\.\d+\.\d+", pragma):
            exact_versions.add(pragma)
        try:
            wanted_sets.append(_specifier_from_solidity_pragma(pragma))
        except Exception:  # pylint: disable=broad-except
            continue

    if len(exact_versions) == 1:
        return next(iter(exact_versions))

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
    if best is not None:
        return best.public

    try:
        available = []
        for v in get_available_versions().keys():
            try:
                available.append(Version(v))
            except InvalidVersion:
                continue
        available = sorted(set(available))
        for v in available:
            if all(v in s for s in wanted_sets):
                best = v
        return best.public if best is not None else None
    except Exception:  # pylint: disable=broad-except
        return None


def _ensure_solc(version: str) -> str:
    if version not in installed_versions():
        ok = install_artifacts([version])
        if not ok:
            raise RuntimeError(f"solc-select could not install {version}")
    return artifact_path(version).absolute().as_posix()


def _pretty_target(value: str) -> str:
    try:
        if os.path.isabs(value):
            return os.path.relpath(value, os.getcwd())
    except Exception:  # pylint: disable=broad-except
        return value
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess Solidity/Vyper targets and output per-function direct call edges (A -> B).",
        usage="contract-preprocess <target> [flag]",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Solidity/Vyper file, project directory, or verified address (0x.. or NETWORK:0x..) to process.",
    )
    parser.add_argument(
        "--targets-file",
        default=None,
        help="Path to a newline-separated target list (blank lines and lines starting with # are ignored).",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write output to file (default: stdout).",
    )
    parser.add_argument(
        "--dump-external-dir",
        default=None,
        help="Write one file per external function containing its source plus all reachable functions (transitive).",
    )
    parser.add_argument(
        "--emit-callgraph",
        action="store_true",
        default=False,
        help="Write callgraph DOT/SVG next to --output (out.callgraph.dot/svg).",
    )

    parser.add_argument(
        "--only-visibility",
        default=None,
        help="Comma-separated visibilities to include: external,public,internal,private (default: all).",
    )

    parser.add_argument(
        "--exclude-dependencies",
        action="store_true",
        default=False,
        help="Exclude contracts coming from dependencies.",
    )
    parser.add_argument(
        "--declared-only",
        action="store_true",
        default=False,
        help="Only include functions declared in each contract (exclude inherited).",
    )
    parser.add_argument(
        "--include-shadowed",
        action="store_true",
        default=False,
        help="Include shadowed functions (default: exclude).",
    )

    parser.add_argument(
        "--no-external-calls",
        action="store_true",
        default=False,
        help="Do not include high-level (external) calls in the tree.",
    )
    parser.add_argument(
        "--no-library-calls",
        action="store_true",
        default=False,
        help="Do not include library calls in the tree.",
    )
    parser.add_argument(
        "--no-modifiers",
        action="store_true",
        default=False,
        help="Do not include modifier execution in the tree.",
    )
    parser.add_argument(
        "--no-base-constructors",
        action="store_true",
        default=False,
        help="Do not include explicit base constructor calls in the tree.",
    )
    parser.add_argument(
        "--include-solidity-calls",
        action="store_true",
        default=False,
        help="Include Solidity builtin calls as leaf nodes.",
    )

    parser.add_argument(
        "--no-fail",
        action="store_true",
        default=False,
        help="Best-effort: skip compilation/parsing failures where possible.",
    )

    parser.add_argument(
        "--vyper-version",
        default=None,
        help="Override Vyper compiler version (e.g. 0.3.10). If omitted, tries to infer from the source header.",
    )
    parser.add_argument(
        "--no-auto-install",
        action="store_true",
        default=False,
        help="Do not auto-install missing compiler versions (Vyper).",
    )

    cryticparser.init(parser)
    return parser.parse_args()


def _crytic_kwargs(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Keep CryticCompile/ContractPreprocess kwargs only (strip our tool-only flags).
    """
    kwargs: Dict[str, Any] = dict(vars(args))
    for key in (
        "targets",
        "targets_file",
        "output",
        "dump_external_dir",
        "emit_callgraph",
        "only_visibility",
        "declared_only",
        "include_shadowed",
        "no_external_calls",
        "no_library_calls",
        "no_modifiers",
        "no_base_constructors",
        "include_solidity_calls",
        "vyper_version",
        "no_auto_install",
    ):
        kwargs.pop(key, None)
    return kwargs


def _iter_instances_for_target(
    target: str, args: argparse.Namespace, kwargs: Dict[str, Any]
) -> Tuple[List[ContractPreprocess], List[Dict[str, Any]]]:
    errors: List[Dict[str, Any]] = []

    # AST json inputs (solc --ast-compact-json or legacy ast json)
    if getattr(args, "solc_ast", False) or (target.endswith(".json") and not is_supported(target)):
        globbed = glob.glob(target, recursive=True)
        filenames = glob.glob(os.path.join(target, "*.json"))
        if not filenames:
            filenames = globbed
        instances: List[ContractPreprocess] = []
        for filename in filenames:
            try:
                instances.append(ContractPreprocess(filename, **kwargs))
            except Exception as e:  # pylint: disable=broad-except
                errors.append({"target": filename, "stage": "contract_preprocess", "error": str(e)})
                if not args.no_fail:
                    raise
        return instances, errors

    compile_kwargs = dict(kwargs)
    if (
        os.path.isfile(target)
        and target.endswith(".sol")
        and compile_kwargs.get("solc", "solc") == "solc"
        and not compile_kwargs.get("solc_solcs_bin")
        and not compile_kwargs.get("solc_solcs_select")
    ):
        try:
            closure = _collect_solidity_closure(Path(target))
            solc_version = _pick_solc_version_for_files(closure) or _pick_solc_version_for_files([Path(target)])
            if solc_version:
                compile_kwargs["solc"] = _ensure_solc(solc_version)
        except Exception as e:  # pylint: disable=broad-except
            errors.append({"target": target, "stage": "solc-select", "error": str(e)})
            if not args.no_fail:
                raise

    try:
        compilations: List[CryticCompile] = compile_all(target, **compile_kwargs)
    except Exception as e:  # pylint: disable=broad-except
        errors.append({"target": target, "stage": "compile_all", "error": str(e)})
        if not args.no_fail:
            raise
        return [], errors

    instances = []
    for compilation in compilations:
        try:
            instances.append(ContractPreprocess(compilation, **kwargs))
        except Exception as e:  # pylint: disable=broad-except
            errors.append({"target": getattr(compilation, "target", target), "stage": "contract_preprocess", "error": str(e)})
            if not args.no_fail:
                raise
    return instances, errors


def _load_targets(args: argparse.Namespace) -> List[str]:
    targets: List[str] = []
    if args.targets_file:
        with open(args.targets_file, "r", encoding="utf8") as f:
            for line in f:
                t = line.strip()
                if not t or t.startswith("#"):
                    continue
                targets.append(t)
    targets.extend(args.targets or [])
    # preserve order, de-dup
    seen = set()
    uniq: List[str] = []
    for t in targets:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def main() -> None:
    args = _parse_args()
    targets = _load_targets(args)
    if not targets:
        raise SystemExit("No targets provided. Pass targets as arguments or via --targets-file.")

    visibilities: Optional[List[str]] = None
    if args.only_visibility:
        visibilities = [v.strip() for v in args.only_visibility.split(",") if v.strip()]

    result: Dict[str, Any] = {
        "tool": "contract-preprocess",
        "targets": targets,
        "compilations": [],
    }

    kwargs = _crytic_kwargs(args)
    all_errors: List[Dict[str, Any]] = []
    dump_external_base = Path(args.dump_external_dir).resolve() if args.dump_external_dir else None

    for target in targets:
        if os.path.isfile(target) and target.endswith(".vy"):
            try:
                vy = preprocess_vyper_file(
                    Path(target),
                    vyper_version=args.vyper_version,
                    auto_install=not args.no_auto_install,
                    include_external_calls=not args.no_external_calls,
                    include_solidity_calls=args.include_solidity_calls,
                )
                if visibilities is not None:
                    wanted = set(visibilities)
                    for k in list(vy["functions"].keys()):
                        if k not in wanted:
                            vy["functions"][k] = []
                result["compilations"].append(
                    {
                        "target": target,
                        "contracts": [{"name": vy["contract_name"], "functions": vy["functions"]}],
                    }
                )
            except Exception as e:  # pylint: disable=broad-except
                all_errors.append({"target": target, "stage": "vyper", "error": str(e)})
                if not args.no_fail:
                    raise
            continue

        instances, errors = _iter_instances_for_target(target, args, kwargs)
        all_errors.extend(errors)
        for instance in instances:
            contracts = instance.contracts
            if args.exclude_dependencies:
                filtered = []
                for c in contracts:
                    try:
                        if not c.is_from_dependency():
                            filtered.append(c)
                    except Exception:  # pylint: disable=broad-except
                        filtered.append(c)
                contracts = filtered

            contracts_sorted = sorted(
                contracts,
                key=lambda c: (
                    c.name,
                    (
                        getattr(
                            getattr(getattr(c, "source_mapping", None), "filename", None), "absolute", ""
                        )
                        or ""
                    ),
                ),
            )

            compilation: Dict[str, Any] = {
                "target": _pretty_target(instance.crytic_compile.target) if instance.crytic_compile else _pretty_target(target),
                "contracts": [],
            }

            for contract in contracts_sorted:
                grouped = contract_functions_by_visibility(
                    contract,
                    include_inherited=not args.declared_only,
                    include_shadowed=args.include_shadowed,
                    visibilities=visibilities,
                )

                contract_entry: Dict[str, Any] = {"name": contract.name, "functions": {}}

                for visibility, functions in grouped.items():
                    contract_entry["functions"][visibility] = [
                        build_function_call_edges(
                            f,
                            include_external_calls=not args.no_external_calls,
                            include_library_calls=not args.no_library_calls,
                            include_solidity_calls=args.include_solidity_calls,
                            include_modifiers=not args.no_modifiers,
                            include_base_constructors=not args.no_base_constructors,
                        )
                        for f in functions
                    ]

                if any(contract_entry["functions"].get(v) for v in contract_entry["functions"]):
                    compilation["contracts"].append(contract_entry)

                if dump_external_base is not None:
                    try:
                        external_only = contract_functions_by_visibility(
                            contract,
                            include_inherited=not args.declared_only,
                            include_shadowed=args.include_shadowed,
                            visibilities=["external"],
                        )["external"]
                        dump_dir = (
                            dump_external_base / _safe_fs_name(compilation["target"])
                            if len(targets) > 1
                            else dump_external_base
                        )
                        for ext_fn in external_only:
                            _dump_external_function_bundle(
                                ext_fn,
                                dump_dir,
                                include_external_calls=not args.no_external_calls,
                                include_library_calls=not args.no_library_calls,
                                include_solidity_calls=args.include_solidity_calls,
                                include_modifiers=not args.no_modifiers,
                                include_base_constructors=not args.no_base_constructors,
                            )
                    except Exception as e:  # pylint: disable=broad-except
                        all_errors.append(
                            {
                                "target": compilation["target"],
                                "stage": "dump-external",
                                "error": str(e),
                            }
                        )
                        if not args.no_fail:
                            raise

            result["compilations"].append(compilation)

    if all_errors:
        result["errors"] = all_errors

    out = json.dumps(result, indent=2, sort_keys=True) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf8") as f:
            f.write(out)
        if args.emit_callgraph:
            out_path = Path(args.output)
            compilations = result.get("compilations") or []
            if len(compilations) == 1:
                _write_callgraph_dot(compilations[0], out_path.with_suffix(".callgraph.dot"))
            elif len(compilations) > 1:
                cg_dir = out_path.parent / f"{out_path.stem}.callgraph"
                cg_dir.mkdir(parents=True, exist_ok=True)
                for idx, comp in enumerate(compilations):
                    tgt = _safe_fs_name(str(comp.get("target") or f"compilation_{idx}"))
                    _write_callgraph_dot(comp, cg_dir / f"{idx:03d}.{tgt}.dot")
    else:
        if args.emit_callgraph:
            raise SystemExit("--emit-callgraph requires --output")
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
