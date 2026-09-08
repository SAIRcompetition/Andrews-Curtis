"""Shared helpers for the verifier test suite."""

import json
from pathlib import Path

from acms_verify import core

REPO = Path(__file__).resolve().parents[1]
CHALLENGES = REPO / "competition" / "challenges"
MANIFEST_PATH = CHALLENGES / "manifest.json"
MOVE_SPEC_PATH = CHALLENGES / "move_spec.json"
STABLE_MOVE_SPEC_PATH = CHALLENGES / "stable_move_spec.json"
TRAINING_PATH = CHALLENGES / "training_424.json"
STABLE_TRAINING_PATH = CHALLENGES / "stable_training_424.json"
GOLDEN_PATH = CHALLENGES / "golden_vectors.json"
MS1190_PATH = CHALLENGES / "ms1190_metadata.csv"
PRIVATE_MAP_PATH = REPO / "build" / "private" / "challenge_map_private.tsv"
#: Digest of the 10115 ac-v1 instance_hash values as they stood BEFORE
#: the stable track existed.  They must never change again.
AC_HASH_SNAPSHOT_PATH = REPO / "tests" / "data" / \
    "ac_v1_instance_hashes_snapshot.json"

AC_PREFIX = "ac-v1-"
STABLE_PREFIX = "sac-v1-"


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest():
    return load(MANIFEST_PATH)


def load_training():
    return load(TRAINING_PATH)


def load_stable_training():
    return load(STABLE_TRAINING_PATH)


def challenges_by_prefix(manifest, prefix):
    """The manifest's challenges for one track, in file order."""
    return [c for c in manifest["challenges"]
            if c["challenge_id"].startswith(prefix)]


def paired_challenges(manifest):
    """``[(ac_record, sac_record), ...]`` matched on the id number."""
    ac = {c["challenge_id"][len(AC_PREFIX):]: c
          for c in challenges_by_prefix(manifest, AC_PREFIX)}
    sac = {c["challenge_id"][len(STABLE_PREFIX):]: c
           for c in challenges_by_prefix(manifest, STABLE_PREFIX)}
    assert set(ac) == set(sac), "tracks do not cover the same presentations"
    return [(ac[n], sac[n]) for n in sorted(ac)]


def canon_word(word):
    """Lex-min over all rotations of ``word`` and of its inverse."""
    best = None
    for cand in (tuple(word), core.invert(tuple(word))):
        for i in range(len(cand)):
            rot = cand[i:] + cand[:i]
            if best is None or rot < best:
                best = rot
    return best


def canon_pair(relators):
    """Order-insensitive canonical key of a two-relator presentation.

    Two presentations share a key iff they agree up to relator order,
    cyclic rotation, and inversion of either word.  Used only to detect
    duplicates and to join the manifest against MS-1190; it is not part
    of any hash or public artifact.
    """
    return tuple(sorted(canon_word(w) for w in relators))


def ms_initial(n, wv):
    """MS(n, w) initial relators under the frozen D-2 convention
    ``r1 = x w^-1`` (DESIGN.md §1.1), recomputed independently of
    ``build/``."""
    r0 = core.free_reduce([-1] + [2] * n + [1] + [-2] * (n + 1))
    r1 = core.free_reduce((1,) + core.invert(tuple(wv)))
    return [list(r0), list(r1)]


def training_challenge(entry):
    """View a training instance as a verifiable challenge dict.

    Works for both tracks: the entry carries its own
    ``move_spec_version`` and ``target_relators``.
    """
    return {
        "challenge_id": entry["training_id"],
        "move_spec_version": entry["move_spec_version"],
        "generators": entry["generators"],
        "initial_relators": entry["initial_relators"],
        "target_relators": entry["target_relators"],
    }
