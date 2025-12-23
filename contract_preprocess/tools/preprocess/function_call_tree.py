from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union, cast

from contract_preprocess.core.declarations import Contract, FunctionContract
from contract_preprocess.core.declarations.function import Function
from contract_preprocess.core.declarations.solidity_variables import SolidityFunction
from contract_preprocess.core.variables.variable import Variable


@dataclass(frozen=True)
class CallTarget:
    kind: str  # function | variable | solidity | unknown
    label: str
    edge: str  # internal | library | external | solidity
    target: Any
    target_contract: Optional[Contract] = None


def _safe_attr(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name)
    except Exception:  # pylint: disable=broad-except
        return default


def function_display_name(function: Function) -> str:
    if isinstance(function, FunctionContract):
        contract_ctx = _safe_attr(function, "contract", None)
        if contract_ctx is not None:
            return f"{contract_ctx.name}.{function.full_name}"
        return f"{function.contract_declarer.name}.{function.full_name}"
    return function.full_name


def function_uid(function: Function) -> str:
    """
    Unique id for a function *instance* in its contract context.
    ContractPreprocess models inherited functions with contract-specific IR; we include the
    contract context name to avoid collapsing distinct instances.
    """
    if isinstance(function, FunctionContract):
        contract_ctx = _safe_attr(function, "contract", None)
        ctx_name = contract_ctx.name if contract_ctx is not None else function.contract_declarer.name
        return f"{ctx_name}::{function.canonical_name}"
    return function_display_name(function)


def _iter_call_targets(function: Function) -> Iterable[CallTarget]:
    # Modifiers (executed as part of the function body)
    for mod in getattr(function, "modifiers", []):
        if isinstance(mod, Function):
            yield CallTarget(kind="function", label=function_display_name(mod), edge="modifier", target=mod)
        elif mod is not None:
            yield CallTarget(kind="unknown", label=str(mod), edge="modifier", target=mod)

    # Explicit base constructors (constructor-only; may be empty)
    for base_ctor in getattr(function, "explicit_base_constructor_calls", []):
        if isinstance(base_ctor, Function):
            yield CallTarget(
                kind="function",
                label=function_display_name(base_ctor),
                edge="base-constructor",
                target=base_ctor,
            )
        elif base_ctor is not None:
            yield CallTarget(kind="unknown", label=str(base_ctor), edge="base-constructor", target=base_ctor)

    # Internal calls (includes SolidityFunction)
    for ir in getattr(function, "internal_calls", []):
        target = _safe_attr(ir, "function", None)
        if isinstance(target, Function):
            yield CallTarget(kind="function", label=function_display_name(target), edge="internal", target=target)
        elif isinstance(target, SolidityFunction):
            yield CallTarget(kind="solidity", label=target.name, edge="solidity", target=target)
        elif target is not None:
            yield CallTarget(kind="unknown", label=str(target), edge="internal", target=target)

    # Library calls
    for ir in getattr(function, "library_calls", []):
        target = _safe_attr(ir, "function", None)
        if isinstance(target, Function):
            yield CallTarget(kind="function", label=function_display_name(target), edge="library", target=target)
        elif target is not None:
            yield CallTarget(kind="unknown", label=str(target), edge="library", target=target)

    # High level calls: list[(Contract, HighLevelCall)]
    for external_contract, ir in getattr(function, "high_level_calls", []):
        target = _safe_attr(ir, "function", None)
        if isinstance(target, Function):
            yield CallTarget(
                kind="function",
                label=function_display_name(target),
                edge="external",
                target=target,
                target_contract=external_contract,
            )
        elif isinstance(target, Variable):
            yield CallTarget(
                kind="variable",
                label=f"{external_contract.name}.{target.name}",
                edge="external",
                target=target,
                target_contract=external_contract,
            )
        elif target is not None:
            yield CallTarget(
                kind="unknown",
                label=f"{external_contract.name}.{target}",
                edge="external",
                target=target,
                target_contract=external_contract,
            )


def iter_call_targets(function: Function) -> Iterable[CallTarget]:
    """
    Yield direct call targets (no recursion).
    """
    yield from _iter_call_targets(function)


def build_function_call_edges(
    root: Function,
    *,
    include_external_calls: bool = True,
    include_library_calls: bool = True,
    include_solidity_calls: bool = False,
    include_modifiers: bool = True,
    include_base_constructors: bool = True,
) -> Dict[str, Any]:
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

    def node_for_function(function: Function) -> Dict[str, Any]:
        contract_ctx = _safe_attr(function, "contract", None)
        contract_ctx_name = contract_ctx.name if contract_ctx is not None else None
        contract_decl = (
            function.contract_declarer.name if isinstance(function, FunctionContract) else None
        )
        return {
            "kind": "function",
            "id": function_uid(function),
            "name": function.full_name,
            "display": function_display_name(function),
            "visibility": _safe_attr(function, "visibility", None),
            "contract_context": contract_ctx_name,
            "declared_in": contract_decl,
            "is_constructor": bool(_safe_attr(function, "is_constructor", False)),
            "is_fallback": bool(_safe_attr(function, "is_fallback", False)),
            "is_receive": bool(_safe_attr(function, "is_receive", False)),
            "is_shadowed": bool(_safe_attr(function, "is_shadowed", False)),
            "calls": [],
        }

    root_node = node_for_function(root)
    targets = [t for t in iter_call_targets(root) if should_keep_edge(t.edge)]

    # De-duplicate by a stable key; we don't care about call count.
    seen: Set[Tuple[str, str, str]] = set()
    calls: List[Dict[str, Any]] = []

    for t in targets:
        if t.kind == "function" and isinstance(t.target, Function):
            callee = cast(Function, t.target)
            if not _safe_attr(callee, "is_implemented", True):
                # Abstract/interface functions: keep nothing as a function node (no body to analyze).
                # If callers need to preserve the call, they can enable unknown targets elsewhere.
                key = (t.edge, "unknown", function_display_name(callee))
                if key in seen:
                    continue
                seen.add(key)
                calls.append({"kind": "unknown", "edge": t.edge, "display": function_display_name(callee)})
                continue
            key = (t.edge, "function", function_uid(callee))
            if key in seen:
                continue
            seen.add(key)
            calls.append(
                {
                    "kind": "function",
                    "edge": t.edge,
                    "id": function_uid(callee),
                    "name": callee.full_name,
                    "display": function_display_name(callee),
                    "visibility": _safe_attr(callee, "visibility", None),
                    "contract_context": _safe_attr(_safe_attr(callee, "contract", None), "name", None),
                    "declared_in": callee.contract_declarer.name if isinstance(callee, FunctionContract) else None,
                }
            )
        elif t.kind == "variable" and isinstance(t.target, Variable):
            key = (t.edge, "variable", t.label)
            if key in seen:
                continue
            seen.add(key)
            calls.append(
                {
                    "kind": "variable",
                    "edge": t.edge,
                    "name": t.target.name,
                    "display": t.label,
                    "contract": t.target_contract.name if t.target_contract else None,
                }
            )
        elif t.kind == "solidity" and isinstance(t.target, SolidityFunction):
            key = (t.edge, "solidity", t.target.name)
            if key in seen:
                continue
            seen.add(key)
            calls.append({"kind": "solidity", "edge": t.edge, "name": t.target.name})
        else:
            key = (t.edge, "unknown", t.label)
            if key in seen:
                continue
            seen.add(key)
            calls.append({"kind": "unknown", "edge": t.edge, "display": t.label})

    calls.sort(key=lambda c: (c.get("edge") or "", c.get("kind") or "", c.get("display") or c.get("name") or ""))
    root_node["calls"] = calls
    return root_node


def contract_functions_by_visibility(
    contract: Contract,
    *,
    include_inherited: bool = True,
    include_shadowed: bool = False,
    visibilities: Optional[Sequence[str]] = None,
) -> Dict[str, List[FunctionContract]]:
    wanted = set(visibilities) if visibilities else {"external", "public", "internal", "private"}
    functions = contract.functions if include_inherited else contract.functions_declared
    filtered: List[FunctionContract] = []
    for f in functions:
        if f.visibility not in wanted:
            continue
        if not f.is_implemented:
            continue
        if not include_shadowed and f.is_shadowed and not f.is_fallback:
            continue
        filtered.append(f)

    groups: Dict[str, List[FunctionContract]] = {k: [] for k in ["external", "public", "internal", "private"]}
    for f in filtered:
        groups.setdefault(f.visibility, []).append(f)

    for v in groups:
        groups[v].sort(key=lambda fn: (function_display_name(fn), function_uid(fn)))
    return groups
