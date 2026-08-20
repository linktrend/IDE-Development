#!/usr/bin/env python3
"""PKT-08 declarative generated-output closure and finalization gate."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping

GRAPH_RELATIVE_PATH = "core/managed-core/config/generated-output-closure.json"
PACKAGED_GRAPH_RELATIVE_PATH = ".ide-development/config/generated-output-closure.json"
DEFAULT_GRAPH_EXCLUSIONS = frozenset({".github/linktrend-secret-scan-fixtures.json"})
DEFAULT_MAX_PASSES = 3


class ClosureError(ValueError):
    """Fail-closed generated-output closure diagnostic."""

    def __init__(self, code: str, detail: str, **diagnostics: Any) -> None:
        self.code = code
        self.detail = detail
        self.diagnostics = diagnostics
        suffix = f" {json.dumps(diagnostics, sort_keys=True)}" if diagnostics else ""
        super().__init__(f"{code}: {detail}{suffix}")


@dataclass(frozen=True)
class OutputSpec:
    id: str
    output: str
    generator: tuple[str, ...]
    invalidating_sources: tuple[str, ...]
    depends_on: tuple[str, ...]
    additional_outputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeneratedOutputGraph:
    schema_version: int
    max_passes: int
    outputs: tuple[OutputSpec, ...]

    @property
    def output_paths(self) -> frozenset[str]:
        return frozenset(item.output for item in self.outputs)

    def ordered_outputs(self) -> tuple[OutputSpec, ...]:
        by_id = {item.id: item for item in self.outputs}
        pending = {item.id: set(item.depends_on) for item in self.outputs}
        ordered: list[OutputSpec] = []
        while pending:
            ready = sorted(item_id for item_id, deps in pending.items() if not deps)
            if not ready:
                raise ClosureError(
                    "ambiguous_dependency",
                    "generated-output dependency graph contains a cycle",
                    outputs=sorted(pending),
                )
            for item_id in ready:
                ordered.append(by_id[item_id])
                pending.pop(item_id)
            for deps in pending.values():
                deps.difference_update(ready)
        return tuple(ordered)


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClosureError("ambiguous_dependency", f"{label} must be non-empty")
    rel = PurePosixPath(value)
    if rel.is_absolute() or ".." in rel.parts or "\\" in value:
        raise ClosureError("ambiguous_dependency", f"{label} must be repository-relative", value=value)
    return rel.as_posix()


def _resolve_graph_path(root: Path, graph_path: str) -> Path:
    requested = root / graph_path
    if requested.is_file() or graph_path != GRAPH_RELATIVE_PATH:
        return requested
    packaged = root / PACKAGED_GRAPH_RELATIVE_PATH
    return packaged if packaged.is_file() else requested


def load_graph(repo_root: Path | str, graph_path: str = GRAPH_RELATIVE_PATH) -> GeneratedOutputGraph:
    root = Path(repo_root).resolve()
    path = _resolve_graph_path(root, graph_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClosureError("graph_invalid", f"cannot read generated-output graph: {graph_path}") from exc
    if not isinstance(payload, Mapping) or payload.get("schemaVersion") != 1 or payload.get("kind") != "generated-output-closure":
        raise ClosureError("graph_invalid", "generated-output graph identity is invalid")
    raw_outputs = payload.get("outputs")
    if not isinstance(raw_outputs, list) or not raw_outputs:
        raise ClosureError("graph_invalid", "generated-output graph requires outputs")
    max_passes = payload.get("maxPasses", DEFAULT_MAX_PASSES)
    if not isinstance(max_passes, int) or isinstance(max_passes, bool) or max_passes < 1 or max_passes > 10:
        raise ClosureError("graph_invalid", "maxPasses must be between one and ten")

    outputs: list[OutputSpec] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, raw in enumerate(raw_outputs):
        if not isinstance(raw, Mapping):
            raise ClosureError("graph_invalid", f"outputs[{index}] must be an object")
        output_id = raw.get("id")
        if not isinstance(output_id, str) or not output_id.strip() or output_id in ids:
            raise ClosureError("ambiguous_dependency", f"duplicate or invalid output id at outputs[{index}]")
        output_rel = _safe_relative(raw.get("output"), f"outputs[{index}].output")
        if output_rel in paths:
            raise ClosureError("ambiguous_dependency", f"multiple generators own {output_rel}")
        command = raw.get("generator")
        if not isinstance(command, list) or not command or any(not isinstance(item, str) or not item for item in command):
            raise ClosureError("ambiguous_dependency", f"outputs[{index}].generator must be an argv array")
        sources = raw.get("invalidatingSources")
        if not isinstance(sources, list) or not sources or any(not isinstance(item, str) or not item for item in sources):
            raise ClosureError("ambiguous_dependency", f"invalidating source set missing for {output_rel}")
        depends = raw.get("dependsOn", [])
        if not isinstance(depends, list) or any(not isinstance(item, str) or not item for item in depends):
            raise ClosureError("ambiguous_dependency", f"dependsOn must be an array for {output_rel}")
        additional = raw.get("additionalOutputs", [])
        if not isinstance(additional, list) or any(not isinstance(item, str) or not item for item in additional):
            raise ClosureError("ambiguous_dependency", f"additionalOutputs must be an array for {output_rel}")
        ids.add(output_id)
        paths.add(output_rel)
        outputs.append(
            OutputSpec(
                id=output_id,
                output=output_rel,
                generator=tuple(command),
                invalidating_sources=tuple(sources),
                depends_on=tuple(depends),
                additional_outputs=tuple(additional),
            )
        )
    unknown = sorted({dep for item in outputs for dep in item.depends_on if dep not in ids})
    if unknown:
        raise ClosureError("ambiguous_dependency", "dependency references unknown output", dependencies=unknown)
    graph = GeneratedOutputGraph(1, max_passes, tuple(outputs))
    graph.ordered_outputs()
    return graph


def _git_index_entries(root: Path) -> list[tuple[str, str, str]]:
    result = subprocess.run(
        ["git", "ls-files", "-s", "-z", "--"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ClosureError("git_identity_failure", (result.stderr or result.stdout).decode("utf-8", "replace").strip())
    entries: list[tuple[str, str, str]] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            meta, path_bytes = raw.split(b"\t", 1)
            mode, oid, stage = meta.split(b" ", 2)
        except ValueError as exc:
            raise ClosureError("git_identity_failure", "cannot parse git index identity") from exc
        entries.append((path_bytes.decode("utf-8"), mode.decode("ascii"), f"{oid.decode('ascii')}:{stage.decode('ascii')}"))
    return entries


def _expanded_exclusions(root: Path, graph: GeneratedOutputGraph) -> frozenset[str]:
    exact = set(graph.output_paths)
    for rel in _walk_files(root, exact):
        if any(_glob_matches(rel, pattern) for spec in graph.outputs for pattern in spec.additional_outputs):
            exact.add(rel)
    return frozenset(exact)


def _graph_exclusions(root: Path, graph_path: str | None) -> frozenset[str]:
    if graph_path is None:
        return DEFAULT_GRAPH_EXCLUSIONS
    try:
        return _expanded_exclusions(root, load_graph(root, graph_path))
    except ClosureError:
        return DEFAULT_GRAPH_EXCLUSIONS


def candidate_source_tree(root: Path | str, graph_path: str | None = GRAPH_RELATIVE_PATH) -> str:
    """Return a stable tracked-content identity excluding generated outputs."""
    checkout = Path(root).resolve()
    exclusions = _graph_exclusions(checkout, graph_path)
    digest = hashlib.sha1()
    for path, mode, identity in sorted(_git_index_entries(checkout)):
        if path in exclusions:
            continue
        oid = identity.split(":", 1)[0]
        digest.update(mode.encode("ascii"))
        digest.update(b" ")
        digest.update(oid.encode("ascii"))
        digest.update(b" ")
        digest.update(path.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _walk_files(root: Path, exclusions: Iterable[str]) -> list[str]:
    excluded = set(exclusions)
    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = _relative(root, path)
        if rel in excluded or any(part in {".git", "build", "__pycache__", ".linktrend"} for part in PurePosixPath(rel).parts):
            continue
        result.append(rel)
    return sorted(result)


def _glob_matches(rel: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/")
    if normalized in {"**", "**/*"}:
        return True
    if normalized.startswith("**/"):
        normalized = normalized[3:]
        if fnmatch.fnmatchcase(rel, normalized) or PurePosixPath(rel).match(normalized):
            return True
    if normalized.endswith("/**"):
        return rel == normalized[:-3].rstrip("/") or rel.startswith(normalized[:-2])
    return fnmatch.fnmatchcase(rel, normalized) or PurePosixPath(rel).match(normalized)


def _source_paths(root: Path, spec: OutputSpec, exclusions: frozenset[str]) -> list[str]:
    files = _walk_files(root, exclusions)
    paths = [rel for rel in files if any(_glob_matches(rel, pattern) for pattern in spec.invalidating_sources)]
    if not paths:
        raise ClosureError(
            "ambiguous_dependency",
            f"invalidating source set matches no files for {spec.output}",
            output=spec.output,
            sourceSet=list(spec.invalidating_sources),
        )
    return paths


def _digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _source_digest(root: Path, paths: Iterable[str]) -> str:
    values = {rel: _digest_file(root / rel) for rel in paths}
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _output_digests(root: Path, graph: GeneratedOutputGraph) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for spec in graph.outputs:
        path = root / spec.output
        result[spec.output] = _digest_file(path) if path.is_file() and not path.is_symlink() else None
        for rel in _walk_files(root, {spec.output}):
            if any(_glob_matches(rel, pattern) for pattern in spec.additional_outputs):
                result[rel] = _digest_file(root / rel)
    return result


def _declared_output_paths(root: Path, graph: GeneratedOutputGraph) -> list[str]:
    return sorted(_expanded_exclusions(root, graph))


def _git_dirty(root: Path, rel: str) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", rel],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return bool(result.returncode == 0 and result.stdout.strip())


def _diagnostic(
    code: str,
    spec: OutputSpec,
    *,
    expected_digest: str | None,
    observed_digest: str | None,
    expected_tree: str,
    observed_tree: str,
    detail: str,
) -> ClosureError:
    return ClosureError(
        code,
        detail,
        output=spec.output,
        generator=list(spec.generator),
        expectedDigest=expected_digest,
        observedDigest=observed_digest,
        expectedTree=expected_tree,
        observedTree=observed_tree,
        invalidatingSources=list(spec.invalidating_sources),
    )


def close_generated_outputs(
    repo_root: Path | str,
    *,
    graph_path: str = GRAPH_RELATIVE_PATH,
    post_generation_hook: Callable[[], None] | None = None,
    _require_clean_outputs: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    graph = load_graph(root, graph_path)
    exclusions = _expanded_exclusions(root, graph)
    if _require_clean_outputs:
        dirty = sorted(rel for rel in _declared_output_paths(root, graph) if _git_dirty(root, rel))
        if dirty:
            raise ClosureError("dirty_output", "generated output is already dirty", outputs=dirty)
    source_maps = {
        spec.id: _source_paths(root, spec, exclusions)
        for spec in graph.outputs
    }
    source_before = {
        spec.id: _source_digest(root, source_maps[spec.id])
        for spec in graph.outputs
    }
    tree_before = candidate_source_tree(root, graph_path)
    output_before = _output_digests(root, graph)
    observed_tree = tree_before
    passes = 0
    for passes in range(1, graph.max_passes + 1):
        for spec in graph.ordered_outputs():
            try:
                completed = subprocess.run(
                    list(spec.generator),
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            except OSError as exc:
                raise _diagnostic(
                    "generator_failure",
                    spec,
                    expected_digest=output_before.get(spec.output),
                    observed_digest=_output_digests(root, graph).get(spec.output),
                    expected_tree=tree_before,
                    observed_tree=observed_tree,
                    detail=str(exc),
                ) from exc
            if completed.returncode:
                detail = (completed.stderr or completed.stdout or "generator failed").strip()[-1000:]
                raise _diagnostic(
                    "generator_failure",
                    spec,
                    expected_digest=output_before.get(spec.output),
                    observed_digest=_output_digests(root, graph).get(spec.output),
                    expected_tree=tree_before,
                    observed_tree=observed_tree,
                    detail=detail,
                )
            path = root / spec.output
            if not path.is_file() or path.is_symlink():
                raise _diagnostic(
                    "generator_failure",
                    spec,
                    expected_digest=output_before.get(spec.output),
                    observed_digest=None,
                    expected_tree=tree_before,
                    observed_tree=observed_tree,
                    detail="generator did not produce a physical output",
                )

        if post_generation_hook is not None:
            command_output_digests = _output_digests(root, graph)
            post_generation_hook()
            after_hook_outputs = _output_digests(root, graph)
            if command_output_digests != after_hook_outputs:
                changed = sorted(
                    path for path in command_output_digests
                    if command_output_digests[path] != after_hook_outputs[path]
                )
                raise ClosureError(
                    "post_generation_mutation",
                    "generated output changed after generator closure",
                    outputs=changed,
                    expectedDigest=command_output_digests,
                    observedDigest=after_hook_outputs,
                    expectedTree=tree_before,
                    observedTree=candidate_source_tree(root, graph_path),
                )

        tree_after = candidate_source_tree(root, graph_path)
        source_after = {
            spec.id: _source_digest(root, source_maps[spec.id])
            for spec in graph.outputs
        }
        if source_after != source_before or tree_after != tree_before:
            raise ClosureError(
                "post_generation_mutation",
                "invalidating source changed during generator closure",
                expectedTree=tree_before,
                observedTree=tree_after,
                expectedDigest=source_before,
                observedDigest=source_after,
            )
        output_after = _output_digests(root, graph)
        if output_after == output_before:
            return {
                "ok": True,
                "passes": passes,
                "generatorOrder": [spec.id for spec in graph.ordered_outputs()],
                "sourceTree": tree_after,
                "invalidatingSources": {
                    spec.id: source_maps[spec.id] for spec in graph.outputs
                },
                "outputDigests": output_after,
            }
        output_before = output_after
        observed_tree = tree_after
    raise ClosureError(
        "non_convergence",
        "generated outputs did not reach a fixed point",
        expectedTree=tree_before,
        observedTree=observed_tree,
        expectedDigest=source_before,
        observedDigest=output_before,
        passes=graph.max_passes,
    )


def _copy_for_verify(source: Path, destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {"build", "__pycache__"}}

    shutil.copytree(source, destination, symlinks=True, ignore=ignore)


def verify_generated_outputs(
    repo_root: Path | str,
    *,
    graph_path: str = GRAPH_RELATIVE_PATH,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    graph = load_graph(root, graph_path)
    dirty = sorted(rel for rel in _declared_output_paths(root, graph) if _git_dirty(root, rel))
    if dirty:
        raise ClosureError("dirty_output", "generated output is dirty before finalization", outputs=dirty)
    observed = _output_digests(root, graph)
    with tempfile.TemporaryDirectory(prefix="pkt08-closure-") as temp:
        clone = Path(temp) / "repo"
        _copy_for_verify(root, clone)
        expected_result = close_generated_outputs(
            clone,
            graph_path=graph_path,
            _require_clean_outputs=False,
        )
        expected = _output_digests(clone, graph)
    mismatches = [
        spec
        for spec in graph.outputs
        if observed.get(spec.output) != expected.get(spec.output)
    ]
    if mismatches:
        spec = mismatches[0]
        raise _diagnostic(
            "stale_output",
            spec,
            expected_digest=expected.get(spec.output),
            observed_digest=observed.get(spec.output),
            expected_tree=str(expected_result.get("sourceTree") or ""),
            observed_tree=candidate_source_tree(root, graph_path),
            detail="working-tree output does not match deterministic generator result",
        )
    return {
        "ok": True,
        "generatorOrder": expected_result["generatorOrder"],
        "sourceTree": expected_result["sourceTree"],
        "outputDigests": observed,
    }


def _generate_secret_scan_fixtures(repo_root: Path) -> int:
    declaration = repo_root / ".github" / "linktrend-secret-scan-fixtures.json"
    payload = json.loads(declaration.read_text(encoding="utf-8"))
    payload["candidateTree"] = candidate_source_tree(repo_root)
    declaration.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", default=GRAPH_RELATIVE_PATH)
    parser.add_argument("--close", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--generate-fixtures", action="store_true")
    args = parser.parse_args(argv)
    root = Path.cwd().resolve()
    try:
        if args.generate_fixtures:
            return _generate_secret_scan_fixtures(root)
        result = verify_generated_outputs(root, graph_path=args.graph) if not args.close else close_generated_outputs(root, graph_path=args.graph)
    except ClosureError as exc:
        print(json.dumps({"ok": False, "code": exc.code, "detail": exc.detail, **exc.diagnostics}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
