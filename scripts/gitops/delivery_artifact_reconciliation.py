#!/usr/bin/env python3
"""Safe stale delivery-artifact reconciliation (WP-U08 / AC-U08-01–06).

Inventory managed PRs, branches, worktrees, and repository-root runtime
residue. Classify with exact commit/tree/path evidence. Clean only
controller-owned empty or tree-equivalent superseded artifacts. Preserve
every unique, uncommitted, partially integrated, unknown, worker, or
protected artifact for an explicit decision. Never leave repository-root
runtime residue: success deletes transients; failure retains diagnostics
in the ignored controller state directory.

This module is fail-closed. It does not call GitHub unless a mutator is
injected. Fixtures, mocks, and disposable repositories are the supported
test surfaces.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = 1
STATE_REL = Path(".linktrend") / "controller-state"
PROTECTED_BRANCHES = frozenset({"main", "staging", "development", "HEAD"})
ROOT_RESIDUE_NAMES = frozenset({"gitops-outcome.json", "integrator-result.json"})
TRANSIENT_FILENAMES = frozenset({"outcome.json", "gate-wait.json", "run.json"})
REPORT_FILENAME = "reconciliation-report.json"
FAILURE_DIAGNOSTICS_FILENAME = "failure-diagnostics.json"
RETAINED_RESIDUE_DIRNAME = "retained-root-residue"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
KIND_PR = "pr"
KIND_BRANCH = "branch"
KIND_WORKTREE = "worktree"
KIND_RUNTIME_RESIDUE = "runtime_residue"
KINDS = frozenset({KIND_PR, KIND_BRANCH, KIND_WORKTREE, KIND_RUNTIME_RESIDUE})
OWNER_CONTROLLER = "controller"
OWNER_WORKER = "worker"
OWNER_UNKNOWN = "unknown"
OWNERS = frozenset({OWNER_CONTROLLER, OWNER_WORKER, OWNER_UNKNOWN})
CLASS_EMPTY = "empty"
CLASS_TREE_EQUIVALENT_SUPERSEDED = "tree_equivalent_superseded"
CLASS_PARTIALLY_INTEGRATED = "partially_integrated"
CLASS_UNIQUE_WORK = "unique_work"
CLASS_UNCOMMITTED = "uncommitted"
CLASS_UNKNOWN = "unknown"
CLASS_PROTECTED = "protected"
CLEANABLE_CLASSES = frozenset({CLASS_EMPTY, CLASS_TREE_EQUIVALENT_SUPERSEDED})
ACTION_CLEAN = "clean"
ACTION_PRESERVE_FOR_DECISION = "preserve_for_decision"
ACTION_KEEP = "keep"
ACTION_ALREADY_ABSENT = "already_absent"
MAX_INFRASTRUCTURE_ATTEMPTS = 2


class ReconciliationError(Exception):
    """Structured fail-closed reconciliation error."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class IdentityUncertainty(ReconciliationError):
    """Missing or conflicting identity; never enters an automatic retry loop."""


class InfrastructureError(ReconciliationError):
    """Retryable infrastructure failure; at most two attempts."""


@dataclass(frozen=True)
class Artifact:
    """One inventoried PR, branch, worktree, or runtime residue item."""

    id: str
    kind: str
    name: str
    controller_owned: bool = False
    owner: str = OWNER_UNKNOWN
    head_sha: str | None = None
    tree_sha: str | None = None
    base_sha: str | None = None
    base_tree_sha: str | None = None
    integrated_trees: tuple[str, ...] = ()
    integrated_commits: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    unique_paths: tuple[str, ...] = ()
    integrated_paths: tuple[str, ...] = ()
    uncommitted: bool = False
    commits_ahead: int | None = None
    exists: bool = True
    path: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ReconciliationError("invalid_kind", f"unsupported artifact kind: {self.kind}")
        if self.owner not in OWNERS:
            raise ReconciliationError("invalid_owner", f"unsupported owner: {self.owner}")
        if not self.id or not self.name:
            raise ReconciliationError("invalid_artifact", "id and name are required")


@dataclass(frozen=True)
class Classification:
    classification: str
    reason: str
    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    artifact: Artifact
    classification: Classification
    action: str


CleanFn = Callable[[Artifact], str]


def _valid_sha(value: str | None) -> bool:
    return isinstance(value, str) and bool(SHA40_RE.fullmatch(value))


def _is_protected(name: str) -> bool:
    raw = (name or "").strip()
    if raw in PROTECTED_BRANCHES:
        return True
    # refs/heads/main and origin/development stay protected.
    leaf = raw.rsplit("/", 1)[-1]
    return leaf in PROTECTED_BRANCHES and raw.startswith(("refs/heads/", "origin/", "refs/remotes/"))


def resolve_state_dir(repo: Path, override: str | os.PathLike[str] | None = None) -> Path:
    """Return the ignored controller diagnostic/state directory."""
    if override:
        return Path(override)
    env = (os.environ.get("LINKTREND_CONTROLLER_STATE_DIR") or "").strip()
    if env:
        return Path(env)
    return Path(repo) / STATE_REL


def ensure_state_dir(state_dir: Path) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def inventory_root_residue(repo: Path) -> list[Artifact]:
    """List known controller-generated files sitting on the repository root."""
    root = Path(repo)
    found: list[Artifact] = []
    for name in sorted(ROOT_RESIDUE_NAMES):
        path = root / name
        if path.is_file():
            found.append(
                Artifact(
                    id=f"residue:{name}",
                    kind=KIND_RUNTIME_RESIDUE,
                    name=name,
                    controller_owned=True,
                    owner=OWNER_CONTROLLER,
                    path=str(path),
                    exists=True,
                )
            )
    return found


def _move_root_residue_to_state(repo: Path, state_dir: Path) -> list[str]:
    retained: list[str] = []
    dest_root = state_dir / RETAINED_RESIDUE_DIRNAME
    for artifact in inventory_root_residue(repo):
        src = Path(artifact.path or (Path(repo) / artifact.name))
        if not src.is_file():
            continue
        dest_root.mkdir(parents=True, exist_ok=True)
        dest = dest_root / src.name
        shutil.move(str(src), str(dest))
        retained.append(src.name)
    return retained


def _delete_root_residue(repo: Path) -> list[str]:
    removed: list[str] = []
    for artifact in inventory_root_residue(repo):
        src = Path(artifact.path or (Path(repo) / artifact.name))
        if src.is_file():
            src.unlink()
            removed.append(src.name)
    return removed


def _clear_transients(state_dir: Path) -> None:
    for name in TRANSIENT_FILENAMES:
        (state_dir / name).unlink(missing_ok=True)


def finish_success(state_dir: Path, report: Mapping[str, Any]) -> Path:
    """Clean transients after success; keep the auditable report in state dir."""
    ensure_state_dir(state_dir)
    _clear_transients(state_dir)
    return write_json(state_dir / REPORT_FILENAME, report)


def finish_failure(state_dir: Path, report: Mapping[str, Any], *, diagnostics: Mapping[str, Any]) -> Path:
    """Retain diagnostics and the report; do not delete evidence."""
    ensure_state_dir(state_dir)
    write_json(state_dir / FAILURE_DIAGNOSTICS_FILENAME, diagnostics)
    return write_json(state_dir / REPORT_FILENAME, report)


def classify_artifact(artifact: Artifact) -> Classification:
    """Classify one artifact from exact commit/tree/path evidence."""
    evidence = {
        "headSha": artifact.head_sha,
        "treeSha": artifact.tree_sha,
        "baseSha": artifact.base_sha,
        "baseTreeSha": artifact.base_tree_sha,
        "integratedTrees": list(artifact.integrated_trees),
        "changedPaths": list(artifact.changed_paths),
        "uniquePaths": list(artifact.unique_paths),
        "integratedPaths": list(artifact.integrated_paths),
        "commitsAhead": artifact.commits_ahead,
        "uncommitted": artifact.uncommitted,
    }
    if _is_protected(artifact.name):
        return Classification(CLASS_PROTECTED, "protected_branch", evidence)
    if artifact.kind == KIND_RUNTIME_RESIDUE:
        return Classification(CLASS_EMPTY, "controller_runtime_residue", evidence)
    if artifact.uncommitted:
        return Classification(CLASS_UNCOMMITTED, "uncommitted_changes", evidence)
    if artifact.kind in {KIND_PR, KIND_BRANCH, KIND_WORKTREE}:
        if not _valid_sha(artifact.head_sha) or not _valid_sha(artifact.tree_sha):
            return Classification(CLASS_UNKNOWN, "missing_commit_or_tree", evidence)
        if not _valid_sha(artifact.base_tree_sha) and not artifact.integrated_trees:
            return Classification(CLASS_UNKNOWN, "missing_integration_identity", evidence)

    tree = artifact.tree_sha
    base_tree = artifact.base_tree_sha
    ahead = artifact.commits_ahead
    unique = artifact.unique_paths
    integrated_paths = artifact.integrated_paths
    changed = artifact.changed_paths

    if ahead == 0 or (
        tree == base_tree
        and not unique
        and not changed
        and (ahead in (0, None))
        and tree not in artifact.integrated_trees
    ):
        return Classification(CLASS_EMPTY, "empty_diff", evidence)

    if (tree and tree in artifact.integrated_trees) or (
        tree == base_tree and ahead is not None and ahead > 0
    ):
        return Classification(
            CLASS_TREE_EQUIVALENT_SUPERSEDED,
            "tree_matches_integrated_commit",
            evidence,
        )

    if unique and integrated_paths:
        return Classification(
            CLASS_PARTIALLY_INTEGRATED,
            "subset_of_paths_already_integrated",
            evidence,
        )

    if unique or (tree and base_tree and tree != base_tree):
        return Classification(CLASS_UNIQUE_WORK, "unique_tree_or_paths", evidence)

    return Classification(CLASS_UNKNOWN, "insufficient_path_evidence", evidence)


def decide_action(artifact: Artifact, classification: Classification) -> str:
    """Return the fail-closed action. Unique work never becomes a keep/delete choice."""
    if not artifact.exists:
        return ACTION_ALREADY_ABSENT
    if classification.classification == CLASS_PROTECTED:
        return ACTION_KEEP
    if artifact.owner == OWNER_WORKER:
        return ACTION_PRESERVE_FOR_DECISION
    if classification.classification in CLEANABLE_CLASSES and artifact.controller_owned:
        return ACTION_CLEAN
    if classification.classification in {
        CLASS_UNIQUE_WORK,
        CLASS_UNCOMMITTED,
        CLASS_PARTIALLY_INTEGRATED,
        CLASS_UNKNOWN,
    }:
        return ACTION_PRESERVE_FOR_DECISION
    # Not controller-owned empty/superseded residue: preserve, never auto-delete.
    return ACTION_PRESERVE_FOR_DECISION


def classify_inventory(artifacts: Sequence[Artifact]) -> list[Decision]:
    decisions: list[Decision] = []
    for artifact in artifacts:
        classification = classify_artifact(artifact)
        decisions.append(Decision(artifact, classification, decide_action(artifact, classification)))
    return decisions


def _try_clean(mutator: CleanFn, artifact: Artifact) -> str:
    attempts = 0
    last: Exception | None = None
    while attempts < MAX_INFRASTRUCTURE_ATTEMPTS:
        attempts += 1
        try:
            return mutator(artifact)
        except IdentityUncertainty:
            raise
        except InfrastructureError as exc:
            last = exc
            continue
        except ReconciliationError:
            raise
    assert last is not None
    raise last


def default_mutator(repo: Path) -> CleanFn:
    """Filesystem/git mutator for disposable repos. Never calls GitHub."""

    def _clean(artifact: Artifact) -> str:
        if artifact.kind == KIND_RUNTIME_RESIDUE:
            src = Path(artifact.path or (Path(repo) / artifact.name))
            if not src.is_file():
                return ACTION_ALREADY_ABSENT
            if src.resolve().parent != Path(repo).resolve():
                raise IdentityUncertainty("unsafe_residue_path", f"{src} is not repository-root residue")
            src.unlink()
            return ACTION_CLEAN
        if artifact.kind == KIND_WORKTREE:
            wt = Path(artifact.path or "")
            if not wt.exists():
                return ACTION_ALREADY_ABSENT
            result = subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt)],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise InfrastructureError(
                    "worktree_remove_failed",
                    (result.stderr or result.stdout or "git worktree remove failed").strip(),
                )
            return ACTION_CLEAN
        if artifact.kind == KIND_BRANCH:
            result = subprocess.run(
                ["git", "branch", "-D", artifact.name],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                text = (result.stderr or result.stdout or "").strip()
                if "not found" in text.lower() or "unknown" in text.lower():
                    return ACTION_ALREADY_ABSENT
                raise InfrastructureError("branch_delete_failed", text)
            return ACTION_CLEAN
        if artifact.kind == KIND_PR:
            raise IdentityUncertainty(
                "github_mutation_not_injected",
                "PR close requires an injected mutator; live GitHub is not called",
            )
        raise ReconciliationError("unsupported_clean", artifact.kind)

    return _clean


def _checkout_is_dirty(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def reconcile(
    *,
    repo: Path,
    artifacts: Sequence[Artifact],
    apply: bool = False,
    mutator: CleanFn | None = None,
    state_dir: Path | None = None,
    force_failure: str | None = None,
) -> dict[str, Any]:
    """Classify inventory, optionally clean allowed artifacts, and place transients in state dir."""
    repo = Path(repo)
    state = ensure_state_dir(state_dir or resolve_state_dir(repo))
    write_json(state / "run.json", {"schemaVersion": SCHEMA_VERSION, "apply": apply})
    write_json(state / "outcome.json", {"status": "running", "detail": "reconciliation_started"})

    combined = list(artifacts)
    seen_ids = {item.id for item in combined}
    for residue in inventory_root_residue(repo):
        if residue.id not in seen_ids:
            combined.append(residue)
            seen_ids.add(residue.id)

    decisions = classify_inventory(combined)
    rows: list[dict[str, Any]] = []
    cleaned: list[str] = []
    preserved: list[str] = []
    kept: list[str] = []
    already: list[str] = []
    cleaner = mutator or default_mutator(repo)
    applied_any = False
    failure_code: str | None = None
    failure_detail: str | None = None

    try:
        if force_failure:
            raise InfrastructureError("forced_failure", force_failure)
        for decision in decisions:
            artifact = decision.artifact
            classification = decision.classification
            action = decision.action
            applied = False
            result_action = action
            # Root residue is always cleaned on a successful pass. Other
            # kinds require --apply and remain preserved unless allowed.
            should_apply = action == ACTION_CLEAN and (
                apply or artifact.kind == KIND_RUNTIME_RESIDUE
            )
            if should_apply:
                result_action = _try_clean(cleaner, artifact)
                applied = result_action in {ACTION_CLEAN, ACTION_ALREADY_ABSENT}
                applied_any = applied_any or result_action == ACTION_CLEAN
            row = {
                "id": artifact.id,
                "kind": artifact.kind,
                "name": artifact.name,
                "owner": artifact.owner,
                "controllerOwned": artifact.controller_owned,
                "classification": classification.classification,
                "reason": classification.reason,
                "action": result_action if apply else action,
                "plannedAction": action,
                "applied": applied,
                "preservedForDecision": action == ACTION_PRESERVE_FOR_DECISION,
                "evidence": dict(classification.evidence),
            }
            rows.append(row)
            if action == ACTION_PRESERVE_FOR_DECISION:
                preserved.append(artifact.id)
            elif action == ACTION_KEEP:
                kept.append(artifact.id)
            elif action == ACTION_ALREADY_ABSENT:
                already.append(artifact.id)
            elif action == ACTION_CLEAN:
                cleaned.append(artifact.id)

        # Root residue is always controller-generated. Success deletes it so
        # the checkout stays clean even when branch/PR apply is dry-run.
        _delete_root_residue(repo)

        report = _build_report(
            state_dir=state,
            ok=True,
            apply=apply,
            rows=rows,
            cleaned=cleaned,
            preserved=preserved,
            kept=kept,
            already=already,
            diagnostics_retained=False,
            replay=not applied_any and apply,
        )
        finish_success(state, report)
        porcelain = _checkout_is_dirty(repo)
        residue_left = [item.name for item in inventory_root_residue(repo)]
        report["rootResidue"] = residue_left
        report["checkoutDirty"] = porcelain
        if residue_left:
            raise ReconciliationError("root_residue_remaining", ",".join(residue_left))
        write_json(state / REPORT_FILENAME, report)
        return report
    except Exception as exc:
        if isinstance(exc, ReconciliationError):
            failure_code, failure_detail = exc.code, exc.detail
        else:
            failure_code, failure_detail = "reconciliation_failed", str(exc)
        retained = _move_root_residue_to_state(repo, state)
        report = _build_report(
            state_dir=state,
            ok=False,
            apply=apply,
            rows=rows,
            cleaned=cleaned,
            preserved=preserved,
            kept=kept,
            already=already,
            diagnostics_retained=True,
            replay=False,
            error={"code": failure_code, "detail": failure_detail},
        )
        finish_failure(
            state,
            report,
            diagnostics={
                "code": failure_code,
                "detail": failure_detail,
                "retainedRootResidue": retained,
            },
        )
        raise
    finally:
        # Running outcome is a transient; success path already cleared it.
        if failure_code:
            write_json(
                state / "outcome.json",
                {"status": "failed", "detail": failure_code, "message": failure_detail},
            )


def _build_report(
    *,
    state_dir: Path,
    ok: bool,
    apply: bool,
    rows: list[dict[str, Any]],
    cleaned: list[str],
    preserved: list[str],
    kept: list[str],
    already: list[str],
    diagnostics_retained: bool,
    replay: bool,
    error: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "ok": ok,
        "apply": apply,
        "idempotentReplay": replay,
        "stateDir": str(state_dir),
        "diagnosticsRetained": diagnostics_retained,
        "rootResidue": [],
        "checkoutDirty": [],
        "artifacts": rows,
        "cleaned": cleaned,
        "preservedForDecision": preserved,
        "kept": kept,
        "alreadyAbsent": already,
        "error": dict(error) if error else None,
    }


def artifact_from_dict(payload: Mapping[str, Any]) -> Artifact:
    if not isinstance(payload, Mapping):
        raise ReconciliationError("invalid_artifact", "artifact must be an object")
    return Artifact(
        id=str(payload.get("id") or payload.get("name") or ""),
        kind=str(payload.get("kind") or ""),
        name=str(payload.get("name") or ""),
        controller_owned=bool(payload.get("controllerOwned", False)),
        owner=str(payload.get("owner") or OWNER_UNKNOWN),
        head_sha=payload.get("headSha"),
        tree_sha=payload.get("treeSha"),
        base_sha=payload.get("baseSha"),
        base_tree_sha=payload.get("baseTreeSha"),
        integrated_trees=tuple(payload.get("integratedTrees") or ()),
        integrated_commits=tuple(payload.get("integratedCommits") or ()),
        changed_paths=tuple(payload.get("changedPaths") or ()),
        unique_paths=tuple(payload.get("uniquePaths") or ()),
        integrated_paths=tuple(payload.get("integratedPaths") or ()),
        uncommitted=bool(payload.get("uncommitted", False)),
        commits_ahead=payload.get("commitsAhead"),
        exists=bool(payload.get("exists", True)),
        path=payload.get("path"),
    )


def load_inventory(path: Path) -> list[Artifact]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, Mapping):
        rows = data.get("artifacts") or data.get("inventory") or []
    else:
        rows = data
    if not isinstance(rows, list):
        raise ReconciliationError("invalid_inventory", "inventory must be a list")
    return [artifact_from_dict(row) for row in rows]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe stale delivery-artifact reconciliation")
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--inventory", help="JSON inventory of PRs/branches/worktrees")
    parser.add_argument("--state-dir", default="", help="override controller state directory")
    parser.add_argument("--apply", action="store_true", help="clean only allowed controller-owned artifacts")
    parser.add_argument("--json", action="store_true", help="print the reconciliation report")
    args = parser.parse_args(list(argv) if argv is not None else None)
    repo = Path(args.repo).resolve()
    artifacts = load_inventory(Path(args.inventory)) if args.inventory else []
    try:
        report = reconcile(
            repo=repo,
            artifacts=artifacts,
            apply=args.apply,
            state_dir=Path(args.state_dir) if args.state_dir else None,
        )
    except ReconciliationError as exc:
        print(f"FAIL: {exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok={report['ok']} cleaned={len(report['cleaned'])} preserved={len(report['preservedForDecision'])}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
