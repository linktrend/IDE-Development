import json
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_auto_cost_requires_explicit_cost_mode_and_readback():
    policy = json.loads((ROOT / "core/managed-core/content/config/model-routing.json").read_text())
    assert policy["conformance"] == {
        "kind": "restoration",
        "mandatory": True,
        "notOptional": True,
        "omissionEvidence": "The superseded baseline hard-coded third-party/default routes without the original cost-mode and effective-model attestation controls.",
    }
    assert policy["route"] == "auto_cost"
    assert policy["auto"] == {
        "selector": "auto-smart",
        "optimizeFor": "cost",
        "requiredReadback": True,
        "cloudApiDefaultIsSufficient": False,
    }


def test_direct_cursor_routes_precede_third_party_exceptions():
    policy = json.loads((ROOT / "core/managed-core/content/config/model-routing.json").read_text())
    assert policy["directFirstPartyFallbacks"] == {
        "bounded": "composer-2.5",
        "complex": "cursor-grok-4.6-medium",
    }
    assert policy["thirdParty"]["requiresExplicitException"] is True
    assert policy["fast"] is False


def test_bulk_documents_has_exact_task_justified_non_fast_binding():
    policy = json.loads((ROOT / "core/managed-core/content/config/model-routing.json").read_text())
    assert policy["bulkDocuments"] == {
        "modelSlug": "gemini-3.7-flash-medium",
        "fast": False,
        "taskJustifiedOnly": True,
    }
    for relative in (
        "core/agents/route-bulk-documents.md",
        "core/skills/model-routing/SKILL.md",
        "core/managed-core/skills/model-routing/SKILL.md",
    ):
        text = (ROOT / relative).read_text()
        assert "gemini-3.7-flash-medium" in text
        assert "gemini-2.5-flash" not in text
    index = (ROOT / "core/agents/INDEX.yaml").read_text()
    assert "Gemini 3.7 Flash Medium" in index
    assert "Fast=false" in index
    assert "Gemini 2.5 Flash" not in index


def test_skill_rejects_generic_auto_and_requires_attestation():
    skill = (ROOT / "core/managed-core/skills/model-routing/SKILL.md").read_text()
    assert "Cloud API `id=default`, `displayName=Auto` without mode proof" in skill
    assert "retain the effective model id, display name, params and usage pool" in skill
    assert "Fast must be false" in skill


def test_doctrine_identifies_restoration_of_original_mandatory_requirement():
    doctrine = (ROOT / "core/managed-core/content/doctrine/MODEL-ROUTING-POLICY.md").read_text()
    assert "restoration/backfill" in doctrine
    assert "original **mandatory" in doctrine
    assert "Coding Execution" in doctrine
    assert "not a new feature" in doctrine
    assert "Historical omission evidence" in doctrine
