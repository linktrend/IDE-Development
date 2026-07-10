# Factory Operations Common Blueprint

> **Status: Planning only — not implemented.** No Supabase, LiNKbrain, LiNKskills, or factory infrastructure in this blueprint is built until Carlos explicitly starts factory ops work.

**Status:** Locked — Carlos/Lisa alignment 2026-07-10 (design document only; see banner above)  
**Scope:** Website, Automation, and Content factories (operations domain)  
**Out of scope:** Application Factory (LiNKdeveloper dev workflow), Trading (not a factory), LiNKaios (deferred), LiNKdev (legacy)

---

## 1. Purpose

This document defines the **common factory operations blueprint** used by LiNKtrend revenue factories. It is separate from the **Application Factory workflow**, which is the LiNKdeveloper development lifecycle (`Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete`) defined and verified in Stage 1a/1b of this repository.

Operations factories share:

- The same structural skeleton (Program → Module → Stage → Issue → Run)
- The same handoff contract model
- The same QA gate model (shippable work + proof of completion)
- The same internal data architecture (one Postgres database, shared brain/skills/agents registry)
- The same execution stack (ledger canonical, n8n deterministic, Plane optional mirror)

**Module, stage, and issue content varies per factory.** The skeleton does not.

**Goal:** Fully autonomous factory operation. Semi-manual operation exists only while building or testing a factory — it is not the long-term standard.

---

## 2. Spine

```
Trigger → Program → Module → Stage → Issue → Run → Gate → … → Output → Complete
```

| Unit | Definition |
|---|---|
| **Trigger** | Factory controller state (`running` \| `paused` \| `stopped`). Factories run continuously like production lines until paused or stopped. Feeders (new lead, topic signal, pain-point brief) enqueue work only while `running`. |
| **Program** | A major part of a factory — or the whole factory. A factory has one or more Programs. Programs depend on one another. Some run continuously and cyclically (e.g. Content: Distribution completes → Discovery starts next cycle). |
| **Module** | Major action inside a Program; has definition of done. Modules may run concurrently or sequentially within a Program. |
| **Stage** | Checkpointed segment inside a Module. |
| **Issue** | Atomic schedulable work unit. |
| **Run** | One execution of an Issue by code, automation, or agent. |
| **Gate** | QA + handoff check. Must verify **shippable work is done** and **proof of completion** is attached. Blocks downstream until pass. |
| **Output** | Deliverable artifact at a module or program boundary. |
| **Complete** | Program cycle finished for that pass. Factory may immediately re-enter (continuous operation). |

---

## 3. Structural rules

1. Handoff **contracts** required: issue↔issue, stage↔stage, module↔module.
2. **QA gates** block progression — evals verify quality, not warnings only.
3. **OpenClaw factory orchestrator** (one executive agent) oversees all operations factories — not one OpenClaw per factory.
4. **Executor agents** (any type: Agent Zero, CrewAI, OpenClaw sub-agent, n8n, scripts) execute Issues.
5. **Executive agents** are OpenClaws only: factory orchestrator, principal overseer (clone), trading agent (outside this blueprint).
6. **CRM canonical source:** Odoo (CRM + accounting). Postgres stores factory entity refs and Odoo foreign keys — does not duplicate CRM data.
7. **LiNKtrend-System / LiNKaios:** Deferred. Historical workflow maps are reference only, not active architecture.

---

## 4. Handoff mechanism

### 4.1 Three layers (locked)

| Layer | Role | Canonical? |
|---|---|---|
| **Factory Run Ledger** | All handoffs, gate state, proofs | **Yes** |
| **n8n** | Deterministic execution (DB sync, publish, Odoo sync, recycle) | Executor |
| **Plane** | Human observation mirror while LiNKaios is deferred | No — sync from ledger only |

Handoff = **ledger state transition** with contract manifest + proof. Not a human moving a card.

Plane sync is **one-way:** Ledger → Plane. Plane status does not drive factory state.

### 4.2 Gate requirements

Every gate must verify:

1. Output manifest matches output contract schema
2. Shippable artifact exists at `storage_uri` with valid `content_hash`
3. Gate evals pass (objective checks, not subjective review)
4. `proof_ref` attached (logs, screenshots, eval results, completion receipt)

---

## 5. Internal data architecture (ten planes)

The ledger is necessary but not sufficient. All operations factories share these planes in **one Supabase Postgres project** (relational only — no Supabase Storage buckets for factory blobs).

### Plane 1 — Factory Run Ledger (`factory.*`)

Canonical execution spine for all factories.

| Entity | Key fields |
|---|---|
| Factory | `factory_id`, `workflow_domain` (`operations` \| `development`), `controller_state` |
| Program | `program_id`, `factory_id`, `depends_on[]`, `cycle_mode` |
| Module | `module_id`, `program_id`, `definition_of_done` |
| Stage | `stage_id`, `module_id`, entry/exit conditions |
| Issue | `issue_id`, `stage_id`, `status`, `executor_type`, `input_manifest_ref` |
| Run | `run_id`, `issue_id`, `executor_agent_id`, `output_manifest_ref`, `proof_ref` |
| Gate | `gate_id`, `run_id`, `eval_results`, `result`, `shippable_verified` |

**Application Factory** uses the same database with `workflow_domain = 'development'` and gate types `proof`, `review`, `integration` (LiNKdeveloper dev workflow). See `docs/LINKDEVELOPER-STAGE1A-SPEC.md`.

### Plane 2 — Contract & Manifest Registry (`contracts.*`)

| Entity | Role |
|---|---|
| Input contracts | JSON schema per issue type |
| Output contracts | Shippable artifact schema per issue type |
| Gate evals | Check definitions, thresholds, required proof types |
| Manifest instances | Pointers via `storage_uri` |

Contracts are versioned in git; Postgres holds registry + active version pointers.

### Plane 3 — Factory Controller (`factory.controller`)

| State | Behaviour |
|---|---|
| `running` | Feeders enqueue; orchestrator dispatches |
| `paused` | No new dispatches; in-flight runs complete or hold |
| `stopped` | Hard stop; manual restart |

Applies per factory and optionally per program.

### Plane 4 — Entity Spine (`entity.*` + Odoo)

Odoo is canonical for leads, partners, deals, invoices, subscriptions.

| Entity | Postgres role | Odoo link |
|---|---|---|
| `entity.site` | `site_id`, hostname, template, factory state | `res.partner`, sale order |
| `entity.content_asset` | `asset_id`, repository path, suite run IDs | Optional partner/project |
| `entity.automation_sku` | `sku_id`, n8n workflow ref | `product.product` |
| `entity.factory_run` | Top-level run binding | `crm.lead` / opportunity |

Sync via n8n or thin Odoo RPC on gate pass — not duplicate CRM tables in Postgres.

### Plane 5 — Artifact Storage Index (`artifact.*`)

Postgres stores pointers only. Blobs live elsewhere.

| Field | Purpose |
|---|---|
| `storage_uri` | `vps://…`, `gdrive://…`, `repo://…` |
| `content_hash` | sha256 integrity |
| `retention_class` | `hot` \| `archive` \| `delete_on_recycle` |

| Tier | Provider | Use |
|---|---|---|
| Hot | VPS (`/data/factories/` or MinIO on existing host) | Site packages, renders, CMS exports |
| Archive | Google Drive (LiNKdrive) | Backups, client deliverables, cold storage |
| Small/versioned | Git | Manifests, eval configs, contracts |
| **Not used** | Supabase Storage buckets | Cost at factory volume |

### Plane 6 — Agent Registry (`agents.*`)

Registry of who can execute what — agents run on VPS/local; DB records identity and routing.

| Table | Role |
|---|---|
| `agents.registry` | `agent_id`, type (`executive` \| `executor`), platform, status |
| `agents.capabilities` | `agent_id`, `issue_type`, `factory_id` |
| `agents.assignments` | Default executor per factory/program/issue type |
| `agents.heartbeat` | Last seen, load, errors |

**Executive agents (OpenClaw only):**

| ID | Role |
|---|---|
| `oc.factory_orchestrator` | All operations factories |
| `oc.principal_overseer` | Oversees factory orchestrator + trading agent |
| `oc.trading` | Outside this blueprint |

**Executors:** Sub-agents, n8n workflows, scripts — registered as added (e.g. `exec.lead_scout`, `exec.outreach`, `n8n.linksites_publish`).

### Plane 7 — Skills Routing Catalog (`linkskills.*`)

| Table | Role |
|---|---|
| `linkskills.pack_registry` | Skill pack ID, version, repo path |
| `linkskills.issue_routing` | `issue_type` → `skill_pack_id` |
| `linkskills.executions` | Telemetry per run |
| `linkskills.evals` | Eval results for skill improvement |

Skill pack **files** stay in git (`core/skills`, `LiNKskills` repo). DB holds registry + routing.

**JIT loading:** Executor loads only the skill pack for the current issue type — not all skills at startup.

Application Factory routes development skills (TDD, spec-driven, release-readiness) through the same catalog with `workflow_domain = 'development'`.

### Plane 8 — Brain Write Policy (`linkbrain.*`)

| Table | Role |
|---|---|
| `linkbrain.audit_events` | Every gate, handoff, agent action |
| `linkbrain.memory_objects` | Promoted organisational knowledge |
| `linkbrain.promotion_queue` | Gate-passed artifacts awaiting librarian review |

**MVP policy:**

| Event | Action |
|---|---|
| Gate pass with proof | Audit event always |
| Recurring failure pattern | Promotion candidate |
| Approved template/contract change | Promote to organisational brain |
| Raw operational data (lead lists) | Audit only |
| Chat reasoning | Never canonical |

Executive OpenClaws read scoped context bundles. Executors write audit; librarian promotes memory.

### Plane 9 — Plane Mirror (`integrations.plane_*`)

| Table | Role |
|---|---|
| `integrations.plane_project_map` | Factory → Plane project |
| `integrations.plane_issue_map` | Ledger issue → Plane work item |
| `integrations.plane_sync_log` | Sync audit |

Uses existing `link-plane` fork. Carlos observes factory health in Plane while LiNKaios is deferred.

### Plane 10 — n8n Route Table (`integrations.n8n_*`)

| Table | Role |
|---|---|
| `integrations.n8n_workflows` | Workflow ID, webhook URL |
| `integrations.n8n_routes` | `issue_type` → workflow |
| `integrations.n8n_run_log` | Execution cross-ref to ledger `run_id` |

---

## 6. Postgres logical layout

```
linktrend_internal (Supabase Postgres — no storage buckets)

factory.*           — Ledger, controller, gates (operations + development domains)
linkbrain.*         — Audit, memory, promotion
linkskills.*        — Pack registry, routing, telemetry
agents.*            — Registry, capabilities, heartbeat
entity.*            — site_id, asset_id, sku_id + odoo_* refs
contracts.*         — Contract registry
integrations.*      — Odoo sync, Plane mirror, n8n routes
artifact.*          — Storage index (URI + hash)
```

---

## 7. Factory definitions (program maps)

### 7.1 Website Factory (LiNKsites) — 4 Programs

```text
P1 Market & Asset Operations
  → P2 Lead-to-Site Production
  → P3 Sales & Lifecycle
  → P4 Client Success & Growth (parallel after close-win)
  P3 no-close → recycle → P1 asset bucket
```

| Program | Modules (summary) |
|---|---|
| **P1 — Market & Asset Operations** | `sites.niche_setup`, `sites.template_library`, `sites.asset_bucket`, `sites.batch_variants` |
| **P2 — Lead-to-Site Production** | `sites.lead_discovery`, `sites.qualification`, `sites.site_assembly`, `sites.db_interop`, `sites.publish_preview` |
| **P3 — Sales & Lifecycle** | `sites.outreach`, `sites.close`, `sites.recycle`, `sites.operate` |
| **P4 — Client Success & Growth** | `sites.content_refresh`, `sites.seo_ops`, `sites.marketing_posts`, `sites.client_reporting` |

**Executors:** Lead scout and outreach are sub-agents — not OpenClaw executives.  
**Product repo:** `/Users/linktrend/Projects/LiNKsites`  
**Detail spec:** To be written in `docs/LINKSITES-FACTORY-WORKFLOW-SPEC.md` (next step).

### 7.2 Content Factory (LiNKtrend Media) — 3 Programs

```text
P1 Discovery & Research
  → P2 Content Creation (Suite 2 + Suite 3)
  → P3 Distribution (& Engagement deferred)
  P3 complete → cycle → P1
```

| Program | Maps from manual |
|---|---|
| **P1 — Discovery & Research** | Suite 1 — research packets, ready queue (pull model) |
| **P2 — Content Creation** | Suite 2 (OpenMontage long-form) + Suite 3 (derivatives) |
| **P3 — Distribution** | Postiz workflow; engagement deferred (evaluate Postiz native tools first) |

**Source:** `LiNKdrive/Manuals/LiNKtrend Media/linktrend_media_content_creation_engine_manual.md`  
**Detail spec:** Later.

### 7.3 Automation Factory — 3 Programs (outline)

| Program | Purpose |
|---|---|
| **P1 — Pain-Point Discovery** | Scan communities, cluster pains |
| **P2 — Build & Package** | Adapt n8n templates, test, SKU |
| **P3 — Sell & Deliver** | Offer to niche, deploy, operate |

**Detail spec:** Later.

---

## 8. Application Factory (separate workflow, same DB)

| | Operations factories | Application Factory |
|---|---|---|
| Workflow | This blueprint | LiNKdeveloper dev workflow (Stage 1a) |
| Entry | Factory controller + feeders | Intent |
| Domain | `workflow_domain = 'operations'` | `workflow_domain = 'development'` |
| System home | Factory repos + ledger | This repo (IDE Development) |
| Plane mirror | Yes | Yes (Application program filter) |

IDE Development is the **tool** used to finish factory gaps — it is not the operations factory workflow.

---

## 9. Workspace

**LiNKdeveloper workspace** (`~/Projects/Workspaces/LiNKdeveloper.code-workspace`):

1. IDE Development (LiNKdeveloper Stage 1)
2. LiNKsites (Website Factory product)

LiNKtrend-System is **not** in the workspace (LiNKaios deferred).

---

## 10. Implementation order

1. Postgres schema migration (factory ledger + supporting planes) — MVP tables first
2. VPS storage layout (`/data/factories/…`)
3. n8n routes for existing LiNKautowork linksites handles
4. Plane mirror sync (ledger → Plane)
5. Website Factory P1 gaps: template library, asset bucket, batch variants
6. Website Factory P2 gaps: lead scout, qualification, db interop flow
7. Website Factory P3 gaps: outreach sub-agent, recycle workflow
8. Odoo sync on P3 close-win → P4 activation
9. Content / Automation factory specs (detail later)

---

## 11. References

| Document | Role |
|---|---|
| `docs/LINKDEVELOPER-STAGE1A-SPEC.md` | Application Factory / dev workflow |
| `docs/LINKDEVELOPER-STAGE1B-REPORT.md` | Stage 1b semi-manual OS |
| `LiNKsites/docs/reference/LINKSITES_FACTORY_KIT_WORKFLOW.md` | Website kit operations |
| `LiNKdrive/Manuals/LiNKtrend Media/linktrend_media_content_creation_engine_manual.md` | Content factory |
| `LiNKdrive/Manuals/LiNKbrain/linkbrain_manual.md` | Brain architecture |
| `LiNKdrive/Manuals/LiNKskills/linkskills_manual.md` | Skills architecture |

---

## 12. Acceptance

This blueprint is **locked** for factory operations design. Factory variant specs (Website detail, Content detail, Automation detail) slot content into this skeleton without changing the skeleton.

**Approved:** Carlos + Lisa — 2026-07-10
