#!/usr/bin/env node
/**
 * Disposable Phase 2 pipeline transition validator.
 * Fail-closed: non-zero exit leaves state file unchanged.
 *
 * Usage:
 *   node scripts/feasibility/validate-pipeline-transition.mjs \
 *     --state <path> --request-transition <module-id>:<target-state> [--apply]
 *   node scripts/feasibility/validate-pipeline-transition.mjs \
 *     --state <path> --request-issue-done <issue-id> [--apply]
 *   node scripts/feasibility/validate-pipeline-transition.mjs \
 *     --state <path> --set-terminal <release_ready|blocked|cancelled> [--apply]
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MODULE_ORDER = [
  "intake_and_definition",
  "assembly_planning",
  "execution",
  "verification_and_hardening",
  "library_contribution",
  "shipment",
];

const MODULE_STATES = new Set([
  "pending",
  "active",
  "gate_pending",
  "blocked",
  "complete",
]);

function fail(message) {
  console.error(`REJECT: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = {
    state: null,
    requestTransition: null,
    requestIssueDone: null,
    setTerminal: null,
    apply: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--state") args.state = argv[++i];
    else if (a === "--request-transition") args.requestTransition = argv[++i];
    else if (a === "--request-issue-done") args.requestIssueDone = argv[++i];
    else if (a === "--set-terminal") args.setTerminal = argv[++i];
    else if (a === "--apply") args.apply = true;
    else if (a === "--help" || a === "-h") {
      console.log(`Usage:
  node validate-pipeline-transition.mjs --state <path> --request-transition <module-id>:<target-state> [--apply]
  node validate-pipeline-transition.mjs --state <path> --request-issue-done <issue-id> [--apply]
  node validate-pipeline-transition.mjs --state <path> --set-terminal <release_ready|blocked|cancelled> [--apply]`);
      process.exit(0);
    } else fail(`Unknown argument: ${a}`);
  }
  if (!args.state) fail("--state is required");
  return args;
}

function loadState(path) {
  if (!existsSync(path)) fail(`State file missing: ${path}`);
  return JSON.parse(readFileSync(path, "utf8"));
}

function loadGate(statePath, gatePath) {
  if (!gatePath) return null;
  const abs = resolve(dirname(statePath), gatePath);
  if (!existsSync(abs)) return null;
  return JSON.parse(readFileSync(abs, "utf8"));
}

function predecessorComplete(state, moduleId) {
  const idx = MODULE_ORDER.indexOf(moduleId);
  if (idx <= 0) return true;
  const prev = MODULE_ORDER[idx - 1];
  return state.modules[prev]?.state === "complete";
}

function validateCompleteTransition(state, statePath, moduleId) {
  const mod = state.modules[moduleId];
  if (!mod) fail(`Unknown module: ${moduleId}`);

  // Rule 7: Module 6 cannot become complete; terminal is release_ready
  if (moduleId === "shipment") {
    fail(
      "Module shipment cannot transition to complete; terminal status for this scope is release_ready",
    );
  }

  const gate = loadGate(statePath, mod.gatePath);
  if (!gate) fail(`Gate absent for module ${moduleId}`);
  if (gate.verdict === "rejected" || gate.verdict === "fail") {
    fail(`Gate rejected for module ${moduleId}; cannot complete`);
  }
  if (gate.verdict !== "pass" && gate.verdict !== "accepted") {
    fail(`Gate verdict missing or not pass for module ${moduleId}`);
  }

  // Rule 4: Module 1 requires recorded Principal approval
  if (moduleId === "intake_and_definition") {
    const recorded =
      gate.principalApprovalRecorded === true ||
      (Array.isArray(state.principalDecisions) &&
        state.principalDecisions.some(
          (d) =>
            d?.scope === "module1" &&
            (d?.decision === "approved" || d?.verdict === "approved"),
        ));
    if (!recorded) {
      fail(
        "Module intake_and_definition cannot complete without recorded Principal approval",
      );
    }
  }

  // Rule 6: Module 4 cannot complete with unmet Living Document criteria
  if (moduleId === "verification_and_hardening") {
    const unmet = gate.unmetLivingDocumentCriteria || [];
    const stateUnmet = (state.livingDocumentCriteria || []).filter(
      (c) => c.status !== "met",
    );
    if (unmet.length > 0 || stateUnmet.length > 0) {
      fail(
        "Module verification_and_hardening cannot complete with unmet Living Document criteria",
      );
    }
  }
}

function validateActivateTransition(state, moduleId) {
  if (!MODULE_ORDER.includes(moduleId)) fail(`Unknown module: ${moduleId}`);
  if (!predecessorComplete(state, moduleId)) {
    const idx = MODULE_ORDER.indexOf(moduleId);
    const prev = MODULE_ORDER[idx - 1];
    fail(
      `Cannot activate ${moduleId}: predecessor ${prev} is not complete (state=${state.modules[prev]?.state})`,
    );
  }
  const prevIdx = MODULE_ORDER.indexOf(moduleId) - 1;
  if (prevIdx >= 0) {
    const prev = MODULE_ORDER[prevIdx];
    const prevMod = state.modules[prev];
    // Also reject if predecessor gate is rejected even if somehow marked
    if (prevMod?.gateVerdict === "rejected") {
      fail(`Cannot activate ${moduleId}: predecessor gate rejected`);
    }
  }
}

function validateIssueDone(state, issueId) {
  const issue = state.issues?.[issueId];
  if (!issue) fail(`Unknown issue: ${issueId}`);
  if (issue.status === "done") fail(`Issue ${issueId} already done`);

  // Rule 5: reject done without proof, passing independent review, and integration
  if (!issue.proof || issue.proof.status !== "present") {
    fail(`Issue ${issueId} cannot become done without proof`);
  }
  if (!issue.review || issue.review.verdict !== "pass") {
    fail(
      `Issue ${issueId} cannot become done without passing independent review`,
    );
  }
  if (!issue.integration || issue.integration.status !== "integrated") {
    fail(`Issue ${issueId} cannot become done without integration`);
  }
  if (issue.selfReviewed === true) {
    fail(`Issue ${issueId} cannot become done: self-review is rejected`);
  }
}

function applyTransition(state, moduleId, targetState) {
  state.modules[moduleId].state = targetState;
  if (targetState === "complete") {
    state.modules[moduleId].gateVerdict = "pass";
  }
  if (targetState === "active") {
    state.currentModuleId = moduleId;
  }
  state.lastTransitionTimestamp = new Date().toISOString();
  state.lastTransitionActor = "feasibility-validator";
}

function main() {
  const args = parseArgs(process.argv);
  const statePath = resolve(args.state);
  const original = readFileSync(statePath, "utf8");
  const state = JSON.parse(original);

  try {
    if (args.requestIssueDone) {
      validateIssueDone(state, args.requestIssueDone);
      if (args.apply) {
        state.issues[args.requestIssueDone].status = "done";
        state.lastTransitionTimestamp = new Date().toISOString();
        state.lastTransitionActor = "feasibility-validator";
        writeFileSync(statePath, `${JSON.stringify(state, null, 2)}\n`);
      }
      console.log(`OK: issue ${args.requestIssueDone} -> done allowed`);
      process.exit(0);
    }

    if (args.setTerminal) {
      const allowed = new Set(["release_ready", "blocked", "cancelled"]);
      if (!allowed.has(args.setTerminal)) {
        fail(`Invalid terminal state: ${args.setTerminal}`);
      }
      if (args.setTerminal === "release_ready") {
        if (state.modules.shipment?.state !== "gate_pending" &&
            state.modules.shipment?.state !== "active") {
          // Allow if shipment gate passed conceptually via gate_pending + pass
        }
        const gate = loadGate(statePath, state.modules.shipment?.gatePath);
        if (!gate || (gate.verdict !== "pass" && gate.verdict !== "accepted")) {
          fail("Cannot set release_ready without passing shipment gate");
        }
      }
      if (args.apply) {
        state.terminalState = args.setTerminal;
        if (args.setTerminal === "release_ready") {
          state.modules.shipment.state = "gate_pending";
        }
        state.lastTransitionTimestamp = new Date().toISOString();
        state.lastTransitionActor = "feasibility-validator";
        writeFileSync(statePath, `${JSON.stringify(state, null, 2)}\n`);
      }
      console.log(`OK: terminal -> ${args.setTerminal} allowed`);
      process.exit(0);
    }

    if (!args.requestTransition) {
      fail("Provide --request-transition, --request-issue-done, or --set-terminal");
    }

    const [moduleId, targetState] = args.requestTransition.split(":");
    if (!moduleId || !targetState) {
      fail("--request-transition must be <module-id>:<target-state>");
    }
    if (!MODULE_ORDER.includes(moduleId)) fail(`Unknown module: ${moduleId}`);
    if (!MODULE_STATES.has(targetState)) {
      fail(`Unknown target state: ${targetState}`);
    }

    if (targetState === "complete") {
      validateCompleteTransition(state, statePath, moduleId);
    } else if (targetState === "active") {
      validateActivateTransition(state, moduleId);
    } else if (targetState === "gate_pending") {
      // allowed from active only for simplicity
      if (state.modules[moduleId]?.state !== "active") {
        fail(`Cannot move ${moduleId} to gate_pending unless active`);
      }
    }

    // Rule 3: also reject activating next if current not complete — covered above

    if (args.apply) {
      applyTransition(state, moduleId, targetState);
      writeFileSync(statePath, `${JSON.stringify(state, null, 2)}\n`);
    }

    console.log(`OK: ${moduleId} -> ${targetState} allowed`);
    process.exit(0);
  } catch (err) {
    // Ensure state unchanged on unexpected error
    writeFileSync(statePath, original);
    fail(err?.message || String(err));
  }
}

main();
