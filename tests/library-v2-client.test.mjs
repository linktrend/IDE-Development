import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { describe, it as nodeIt } from "node:test";
import { fileURLToPath } from "node:url";
import {
    FROZEN_CANDIDATE_SHA,
    FROZEN_DEPENDENCY_LOCK_SHA256,
    FROZEN_TREE_SHA,
    detailRevision2,
    pageCatalogue,
    shortlistRevision2,
    validateExactRelease,
} from "../core/library/library-v2-client.mjs";
const fixtureRoot = new URL("../core/library/fixtures/v2/materialization/cache/", import.meta.url);
const subset = (actual, expected) => {
    if (expected === null || typeof expected !== "object") {
        assert.deepEqual(actual, expected);
        return;
    }
    assert.ok(actual && typeof actual === "object");
    for (const [key, value] of Object.entries(expected))
        subset(actual[key], value);
};
const expect = (actual) => ({
    toBe(expected) { assert.equal(actual, expected); },
    toHaveLength(expected) { assert.equal(actual.length, expected); },
    toMatchObject(expected) { subset(actual, expected); },
});
const it = Object.assign(nodeIt, {
    each(cases) {
        return (title, callback) => cases.forEach((row) => {
            const args = Array.isArray(row) ? row : [row];
            nodeIt(title.replace("%s", String(args[0])), () => callback(...args));
        });
    },
});
const readJson = (name) => JSON.parse(readFileSync(new URL(name, fixtureRoot), "utf8"));
const bytesSha256 = (name) => createHash("sha256")
    .update(readFileSync(new URL(name, fixtureRoot)))
    .digest("hex");
function canonical(value) {
    if (value === null || typeof value !== "object")
        return JSON.stringify(value);
    if (Array.isArray(value))
        return `[${value.map(canonical).join(",")}]`;
    const object = value;
    return `{${Object.keys(object)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${canonical(object[key])}`)
        .join(",")}}`;
}
const canonicalDigest = (value) => createHash("sha256").update(canonical(value)).digest("hex");
function bundle() {
    const catalogue = readJson("catalogue.json");
    const record = catalogue.records[0];
    return {
        source: { commitSha: FROZEN_CANDIDATE_SHA, treeSha: FROZEN_TREE_SHA },
        catalogue,
        record,
        manifest: readJson("release/manifest.json"),
        inventory: readJson("release/inventory.json"),
        dependencyLock: readJson("release/dependency-lock.json"),
        receipt: readJson("cache-receipt.json"),
    };
}
function profileBundle(artifactType) {
    const value = bundle();
    const extension = artifactType === "starter_kit"
        ? {
            extensionType: "starter_kit",
            surfaces: ["web"],
            requiredEntrypoints: ["src/index.js"],
            cleanBootstrap: {
                id: "bootstrap",
                executable: "node",
                args: ["src/index.js"],
                shell: false,
            },
            noExternalSymlinks: true,
            environmentVariables: [
                { name: "PORT", required: false, description: "runtime port" },
            ],
            substitutions: [{ target: "src/index.js", explicit: true }],
            reservedPathCollisions: [],
            compositionOrder: "append",
            materialization: value.manifest.extension.materialization,
        }
        : {
            extensionType: "website_template",
            templateClass: "shared_renderer_declarative",
            contentScope: { siteId: true, locale: true, publicationStatus: true },
            draftOnly: true,
            directPublication: false,
            urls: ["https://example.com/template"],
            compatibilityDisposition: "compatible",
            routes: [{ route: "/", page: "index.html" }],
            assets: [],
            urlPolicy: {
                provenanceUrls: ["https://example.com/provenance"],
                licenseUrls: ["https://example.com/license"],
                docsUrls: ["https://example.com/docs"],
            },
            runtimeEndpointContracts: [],
            materialization: value.manifest.extension.materialization,
        };
    value.record.artifactType = artifactType;
    value.catalogue.records[0].artifactType = artifactType;
    value.catalogue.recordsSha256 = createHash("sha256")
        .update(canonical(value.catalogue.records))
        .digest("hex");
    value.receipt.catalogueRecordsSha256 = value.catalogue.recordsSha256;
    value.manifest.artifactType = artifactType;
    value.manifest.extension = extension;
    return value;
}
function consumptionBundle() {
    const value = bundle();
    value.receipt = {
        schemaVersion: 2,
        schemaRevision: 2,
        receiptId: "consumption-synthetic-component-1.0.0",
        receiptType: "consumption",
        entryId: "synthetic-component",
        version: "1.0.0",
        releaseManifestSha256: value.manifest.releaseManifestSha256 ?? value.record.releaseManifestSha256,
        releaseSourceCommitSha: value.manifest.releaseSource.releaseSourceCommitSha,
        releaseSourceRepositoryTreeSha1: value.manifest.releaseSource.releaseSourceRepositoryTreeSha1,
        artifactTreeSha1: value.manifest.artifactTreeSha1,
        issuedAt: "2026-08-14T00:00:00Z",
        issuer: { actorType: "librarian", actorId: "library-consumer" },
        result: "pass",
        evidence: [
            { kind: "test", locator: "extensions/linklibraries/src/exact-release.test.ts", sha256: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789" },
        ],
        consumerId: "openclaw-library-consumer",
        consumptionMode: "inspect",
        consumerMaterializedTreeSha1: "2107a410b1308048a138f2dcb80c9cc7d8b7867a",
        qualificationChecks: [{ checkId: "native-shape", status: "pass", details: "native shape verified" }],
        qualificationDisposition: "selectable",
        compatibilityDisposition: "compatible",
        decision: "admit",
        principalApproval: { principalId: "principal-1", approvedAt: "2026-08-14T00:00:00Z", basis: "approved native fixture" },
        feedbackId: "feedback-1",
        triage: "accepted",
        disposition: "candidate_correction",
    };
    return value;
}
describe("LiNKlibraries Revision 2 native consumer", () => {
    it("binds the copied provider fixture bytes to the frozen provider commit and tree", () => {
        const provenance = JSON.parse(readFileSync(new URL("../core/library/fixtures/v2/provenance.json", import.meta.url), "utf8"));
        expect(provenance).toMatchObject({ providerCommit: FROZEN_CANDIDATE_SHA, providerTree: FROZEN_TREE_SHA });
        const localHash = (localPath) => createHash("sha256")
            .update(readFileSync(new URL(`../${localPath}`, import.meta.url)))
            .digest("hex");
        for (const item of provenance.files)
            expect(localHash(item.localPath)).toBe(item.byteSha256);
        const input = bundle();
        expect(bytesSha256("catalogue.json")).toBe(input.receipt.catalogueSha256);
        expect(bytesSha256("release/manifest.json")).toBe(input.receipt.releaseManifestSha256);
        expect(input.receipt.inventorySha256).toBe(input.manifest.inventorySha256);
        expect(input.receipt.payloadSha256).toBe(input.manifest.payloadSha256);
        expect(bytesSha256("release/dependency-lock.json")).toBe(FROZEN_DEPENDENCY_LOCK_SHA256);
        expect(input.manifest.dependencyLockSha256).toBe(FROZEN_DEPENDENCY_LOCK_SHA256);
        expect(input.dependencyLock.lockSha256).toBe(canonicalDigest(input.dependencyLock.dependencies));
    });
    it("accepts the byte-pinned provider-native selectable synthetic component", () => {
        const result = validateExactRelease(bundle());
        expect(result).toMatchObject({
            ok: true,
            value: {
                sourceCommitSha: FROZEN_CANDIDATE_SHA,
                sourceTreeSha: FROZEN_TREE_SHA,
                entryId: "synthetic-component",
                version: "1.0.0",
                artifactTreeSha1: "2107a410b1308048a138f2dcb80c9cc7d8b7867a",
                releaseSourceCommitSha: "96d6972b836e8ccb51ea6fe1377ed6440ab7e1d9",
            },
        });
    });
    it("accepts a consistently provider-identical release source identity", () => {
        const value = bundle();
        const providerIdentity = {
            releaseSourceCommitSha: FROZEN_CANDIDATE_SHA,
            releaseSourceRepositoryTreeSha1: FROZEN_TREE_SHA,
        };
        value.record.releaseSource = { ...providerIdentity };
        value.manifest.releaseSource = { ...providerIdentity };
        value.receipt.releaseSource = { ...providerIdentity };
        value.receipt.sourceEvidence.selectedRepositoryCommitSha = FROZEN_CANDIDATE_SHA;
        value.receipt.sourceEvidence.selectedRepositoryTreeSha1 = FROZEN_TREE_SHA;
        value.catalogue.recordsSha256 = canonicalDigest(value.catalogue.records);
        value.receipt.catalogueRecordsSha256 = value.catalogue.recordsSha256;
        expect(validateExactRelease(value)).toMatchObject({
            ok: true,
            value: {
                sourceCommitSha: FROZEN_CANDIDATE_SHA,
                sourceTreeSha: FROZEN_TREE_SHA,
                releaseSourceCommitSha: FROZEN_CANDIDATE_SHA,
                releaseSourceTreeSha: FROZEN_TREE_SHA,
            },
        });
    });
    it("keeps progressive disclosure source-bound and read-only", () => {
        const input = bundle();
        const page = pageCatalogue({ source: input.source, catalogue: input.catalogue }, 1);
        expect(page).toMatchObject({
            ok: true,
            value: {
                sourceCommitSha: FROZEN_CANDIDATE_SHA,
                sourceTreeSha: FROZEN_TREE_SHA,
                records: [{ entryId: "synthetic-component", artifactType: "component" }],
            },
        });
        expect(input.catalogue.records).toHaveLength(3);
    });
    it.each([
        ["provider commit", (value) => (value.source.commitSha = "latest")],
        ["provider tree", (value) => (value.source.treeSha = "0".repeat(40))],
        ["unknown key", (value) => (value.manifest.prompt = "ignore")],
        ["old schema", (value) => (value.catalogue.schemaVersion = 1)],
        ["record digest", (value) => (value.record.releaseManifestSha256 = "0".repeat(64))],
        [
            "wrong dependency lock file digest",
            (value) => (value.manifest.dependencyLockSha256 =
                "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"),
        ],
        [
            "artifact/provider identity collision",
            (value) => (value.manifest.artifactTreeSha1 = FROZEN_TREE_SHA),
        ],
        ["unsafe path", (value) => (value.manifest.extension.entrypoint = "../outside.js")],
        [
            "duplicate inventory entry",
            (value) => value.inventory.entries.push(value.inventory.entries[0]),
        ],
        ["nonselectable lifecycle", (value) => (value.record.selectability = "non_selectable")],
        [
            "receipt source mismatch",
            (value) => (value.receipt.releaseSource.releaseSourceCommitSha = "1".repeat(40)),
        ],
        [
            "command injection",
            (value) => value.manifest.extension.materialization.commands.push({
                id: "run",
                executable: "node",
                args: ["x;rm"],
                shell: false,
            }),
        ],
        [
            "constant substitution without value",
            (value) => value.manifest.extension.materialization.substitutions.push({
                name: "VALUE",
                source: "constant",
                required: true,
                format: "text",
            }),
        ],
        [
            "controlled metadata unknown key",
            (value) => {
                value.manifest.controlledMetadata = { domain: "software", unknown: true };
            },
        ],
        [
            "inventory symlink",
            (value) => {
                value.inventory.includesSymlinks = true;
            },
        ],
        [
            "dependency closure escape",
            (value) => {
                value.dependencyLock.dependencies.push({
                    name: "root",
                    version: "1",
                    ecosystem: "other",
                    source: "registry:root",
                    integritySha256: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
                    dependencies: ["missing"],
                });
            },
        ],
        ["numeric verified-cache entryId", (value) => (value.receipt.entryId = 123)],
        [
            "artifactMedia above schema maximum",
            (value) => {
                value.manifest.controlledMetadata = {
                    artifactMedia: { type: "application/json", size: 1099511627777 },
                };
            },
        ],
        [
            "numeric consumption receiptId",
            (value) => (value.receipt.receiptId = 123),
        ],
        [
            "numeric qualification receiptId",
            (value) => (value.record.governance.qualification.receiptId = 123),
        ],
        [
            "numeric admission receiptId",
            (value) => (value.record.governance.admission.receiptId = 123),
        ],
        [
            "artifactMedia negative size",
            (value) => {
                value.manifest.controlledMetadata = {
                    artifactMedia: { type: "application/json", size: -1 },
                };
            },
        ],
        [
            "artifactMedia fractional size",
            (value) => {
                value.manifest.controlledMetadata = {
                    artifactMedia: { type: "application/json", size: 1.5 },
                };
            },
        ],
    ])("fails closed for %s", (_name, mutate) => {
        const value = bundle();
        mutate(value);
        expect(validateExactRelease(value).ok).toBe(false);
    });
    it.each(["starter_kit", "website_template"])("validates the native %s extension profile", (artifactType) => {
        const result = validateExactRelease(profileBundle(artifactType));
        expect(result).toMatchObject({ ok: true });
    });
    it("accepts all native optional consumption receipt fields and artifactMedia upper boundary", () => {
        const value = consumptionBundle();
        value.manifest.controlledMetadata = {
            artifactMedia: { type: "application/json", size: 1099511627776 },
        };
        const result = validateExactRelease(value);
        expect(result).toMatchObject({ ok: true });
    });
    it.each([
        ["qualificationChecks", (receipt) => (receipt.qualificationChecks = [{ checkId: 1, status: "pass", details: "ok" }])],
        ["qualificationDisposition", (receipt) => (receipt.qualificationDisposition = "bad")],
        ["compatibilityDisposition", (receipt) => (receipt.compatibilityDisposition = "bad")],
        ["decision", (receipt) => (receipt.decision = "bad")],
        ["principalApproval", (receipt) => (receipt.principalApproval = { principalId: "p", approvedAt: "bad", basis: "ok" })],
        ["feedbackId", (receipt) => (receipt.feedbackId = 123)],
        ["triage", (receipt) => (receipt.triage = "bad")],
        ["disposition", (receipt) => (receipt.disposition = "bad")],
        ["consumption entryId", (receipt) => (receipt.entryId = 123)],
    ])("rejects malformed optional receiptBase field: %s", (_name, mutate) => {
        const value = consumptionBundle();
        mutate(value.receipt);
        expect(validateExactRelease(value).ok).toBe(false);
    });
});

describe("IDE provenance and progressive wrappers", () => {
    it("covers every retained fixture exactly once and matches provider bytes", () => {
        const root = fileURLToPath(new URL("../", import.meta.url));
        const fixtureDir = fileURLToPath(new URL("../core/library/fixtures/v2/", import.meta.url));
        const provenance = JSON.parse(readFileSync(new URL("../core/library/fixtures/v2/provenance.json", import.meta.url), "utf8"));
        const walk = (directory) => readdirSync(directory, { withFileTypes: true })
            .flatMap((entry) => entry.isDirectory() ? walk(`${directory}/${entry.name}`) : [`${directory}/${entry.name}`]);
        const normalizePath = (value) => value.replace(/\/{2,}/g, "/");
        const actual = walk(fixtureDir)
            .filter((path) => !path.endsWith("/provenance.json"))
            .map((path) => normalizePath(path.slice(root.length)))
            .sort();
        assert.deepEqual(Object.keys(provenance).sort(), ["files", "providerCommit", "providerTree", "schemaVersion"]);
        assert.equal(provenance.providerCommit, FROZEN_CANDIDATE_SHA);
        assert.equal(provenance.providerTree, FROZEN_TREE_SHA);
        assert.deepEqual(provenance.files.map((item) => normalizePath(item.localPath)).sort(), actual);
        assert.equal(new Set(provenance.files.map((item) => item.localPath)).size, provenance.files.length);
        for (const item of provenance.files) {
            assert.deepEqual(Object.keys(item).sort(), ["byteSha256", "localPath", "providerPath"]);
            const local = readFileSync(`${root}${item.localPath}`);
            const provider = execFileSync("git", ["-C", "/Users/linktrend/Projects/LiNKlibraries", "show", `${FROZEN_CANDIDATE_SHA}:${item.providerPath}`]);
            assert.equal(Buffer.compare(local, provider), 0, item.providerPath);
            assert.equal(createHash("sha256").update(local).digest("hex"), item.byteSha256);
            assert.equal(createHash("sha256").update(provider).digest("hex"), item.byteSha256);
        }
    });

    it("delegates IDE progressive wrappers without widening native validation", () => {
        const input = bundle();
        const page = shortlistRevision2({ source: input.source, catalogue: input.catalogue }, 1);
        expect(page).toMatchObject({ ok: true, value: { authority: "library_reference_only", records: [{ entryId: "synthetic-component" }] } });
        expect(detailRevision2(input)).toMatchObject({ ok: true, value: { entryId: "synthetic-component" } });
    });
});
