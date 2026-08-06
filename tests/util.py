"""Shared helpers for the verifier test suite."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHALLENGES = REPO / "competition" / "challenges"
MANIFEST_PATH = CHALLENGES / "manifest.json"
MOVE_SPEC_PATH = CHALLENGES / "move_spec.json"
TRAINING_PATH = CHALLENGES / "training_424.json"
GOLDEN_PATH = CHALLENGES / "golden_vectors.json"


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest():
    return load(MANIFEST_PATH)


def load_training():
    return load(TRAINING_PATH)


def training_challenge(entry):
    """View a training instance as a verifiable challenge dict."""
    return {
        "challenge_id": entry["training_id"],
        "move_spec_version": entry["move_spec_version"],
        "generators": entry["generators"],
        "initial_relators": entry["initial_relators"],
        "target_relators": entry["target_relators"],
    }
