# Contract Preprocess Tool

Simple Solidity/Vyper preprocessing tool that compiles a target and outputs **direct function call edges** (A → B).

## Install (optional)

```bash
python -m pip install -e .
```

## Usage

```bash
contract-preprocess <target> -o out.json
```

No install:

```bash
python -m contract_preprocess.tools.preprocess <target> -o out.json
```

### Extra outputs

```bash
contract-preprocess <target> -o out.json --emit-callgraph --dump-external-dir out_external
```

- Callgraph: `out.callgraph.dot` and best-effort `out.callgraph.svg` (requires `dot`).
- External bundles: `out_external/<ContractName>/*.sol` (one file per external function; includes all reachable functions across visibilities; no tree output; abstract/interface functions excluded).

### Batch run (Etherscan/SourceCode)

```bash
python Etherscan/run_all.py
```

Run one (or more) addresses:

```bash
python Etherscan/run_all.py 0x2b083beaac310cc5e190b1d2507038ccb03e7606
```

Common options:
- `--only-visibility external,public,internal,private`
- `--declared-only`
- `--exclude-dependencies`
- `--no-external-calls` / `--no-library-calls` / `--no-modifiers` / `--no-base-constructors`
- `--include-solidity-calls`
- `--no-fail`

Output is JSON with per-contract, per-visibility function lists. Each function has a de-duplicated `calls` list (direct callees only).
# ca_preprocess
