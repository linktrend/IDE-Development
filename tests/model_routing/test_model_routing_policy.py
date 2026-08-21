import json
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_auto_cost_requires_explicit_cost_mode_and_readback():
    policy = json.loads((ROOT / "core/managed-core/content/config/model-routing.json").read_text())
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


def test_skill_rejects_generic_auto_and_requires_attestation():
    skill = (ROOT / "core/managed-core/skills/model-routing/SKILL.md").read_text()
    assert "Cloud API `id=default`, `displayName=Auto` without mode proof" in skill
    assert "retain the effective model id, display name, params and usage pool" in skill
    assert "Fast must be false" in skill
