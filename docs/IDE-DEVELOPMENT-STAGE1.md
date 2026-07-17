# IDE Development — Application Factory Declaration

**Status:** Complete — shipped 2026-07-10. Naming corrected 2026-07-15 (see note below).

## What this is

**IDE Development** is this repository (`IDE Development` on disk, `linktrend/IDE-Development` on GitHub). It is the semi-manual, product-agnostic **Application Factory** operating system — doctrine, artifacts, workflows, contracts, and hybrid skills for building any venture product through the lifecycle `Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete`. It is complete and ready for day-to-day use. It is **not** the operations workflow for any specific Website, Automation, or Content factory — a generic shared blueprint for that was tried and retired (see `docs/ARCHIVE-INDEX.md`); each factory-style product defines its own operations model in its own specification.

## Naming correction (2026-07-15)

This repository was previously branded "LiNKdeveloper" in its own docs, with "Stage 1/2/3" framing describing an autonomy roadmap for *this repo itself* handing off execution to OpenClaw over time. That framing is retired. Current state:

- **IDE Development** (this repo) is the permanent, human-assisted development core used with Cursor/Codex. It does not "evolve into" a more autonomous stage of itself.
- **LiNKdeveloper** is a separate, independent Program and repository (`/Users/linktrend/Projects/LiNKdeveloper`) — a VPS-hosted, mostly-autonomous application factory. It may be *authored* using this repo's `.cursor` surface (same as any other repo in the workspace), but it does not depend on this repo at runtime, and its own doctrine/skills/gates are copied and adapted here, not referenced live.

## Application vs. factory-style products (do not conflate)

The **Application Factory** (this repository) is the shared dev workflow used to build any venture product — entry is **Intent**, and it is agnostic to what that product is. A **factory-style product** (a continuous production line such as a website, automation, or content factory) additionally needs its own operations model — planes, ledger, gates, infrastructure — but that model belongs in the product's own repository/specification, not here. Detail on why the earlier shared attempt was retired: [`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) §8, [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md).

## Deliverables

1. This declaration — this document
2. Operator instructions — [`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)
3. Hybrid skills registry — [`docs/HYBRID-SKILLS-REGISTRY.md`](HYBRID-SKILLS-REGISTRY.md)
4. Retired systems and archive paths — [`docs/ARCHIVE-INDEX.md`](ARCHIVE-INDEX.md)
5. Historical evidence — [`docs/archive/`](archive/README.md)

Automated re-check: `scripts/verify-ide-development.sh`

## Operate from here

**New operators:** start with [`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md).
