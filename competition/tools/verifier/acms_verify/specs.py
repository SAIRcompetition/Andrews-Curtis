"""Move-spec registry: ``move_spec_version`` -> the semantics that implement it.

The Discovery Track covers AC and Stable AC over the same 10,115 presentations:

  ``ac-r2-v1``   rank-2 Andrews-Curtis, target the exact ordered pair
                 (x, y), 14 atomic moves            :mod:`acms_verify.core`
  ``sac-r8-v1``  stable Andrews-Curtis, target the empty presentation,
                 257 atomic moves, rank up to 8     :mod:`acms_verify.stable_core`

A challenge names its spec in ``move_spec_version`` and its
``challenge_id`` prefix (``ac-`` / ``sac-``) selects the problem. A
submission contains only ``challenge_id`` and ``moves``; the official
challenge supplies the spec for verification and certificate hashing.

Everything that needs to branch on a spec — the submission layer, the
golden runner, the CLI, the builders — goes through this registry, so
adding a spec is one entry, not a grep.
"""

import types

from . import canon, core, stable_core


def _entry(module, target, max_rank, id_prefix, file):
    return types.SimpleNamespace(
        move_spec_version=module.MOVE_SPEC_VERSION,
        module=module,
        MOVE_TABLE=module.MOVE_TABLE,
        NUM_MOVES=module.NUM_MOVES,
        move_spec_hash=canon.move_spec_hash(module.MOVE_TABLE),
        target=target,
        max_rank=max_rank,
        id_prefix=id_prefix,
        file=file,
        verify=module.verify,
    )


#: version -> namespace.  Insertion order is the published order (the
#: ``move_specs`` list of the manifest, of competition.yaml and of the
#: golden header): the AC problem first, the Stable AC problem second.
SPECS = {
    core.MOVE_SPEC_VERSION: _entry(
        core, [[1], [2]], 2, "ac-", "move_spec.json"),
    stable_core.MOVE_SPEC_VERSION: _entry(
        stable_core, [], stable_core.MAX_RANK, "sac-",
        "stable_move_spec.json"),
}

#: The published order of the registry, for the ``move_specs`` headers.
SPEC_ORDER = tuple(SPECS)


def get(move_spec_version):
    """Registry lookup.  An unknown version here is a developer error
    (bad manifest / bad golden file), not a contestant error, so it
    raises instead of producing a verdict."""
    try:
        return SPECS[move_spec_version]
    except KeyError:
        raise ValueError("unknown move_spec_version: %r (known: %s)"
                         % (move_spec_version, ", ".join(SPEC_ORDER)))


def verify_challenge(challenge, moves, move_spec_version, limits):
    """Dispatch on the CHALLENGE's spec, then verify.

    The submission layer passes the challenge's own version. The
    explicit version argument also supports internal conformance tests
    for ``E_SPEC_MISMATCH``; it is never a contestant submission field.
    """
    return get(challenge["move_spec_version"]).verify(
        challenge, moves, move_spec_version, limits)


def move_spec_hashes():
    """``{move_spec_version: move_spec_hash}`` for every known spec."""
    return {v: s.move_spec_hash for v, s in SPECS.items()}


def check_move_specs(entries):
    """Validate a manifest/golden ``move_specs`` list against the registry.

    Returns a list of human-readable problems; empty means agreement.
    """
    problems = []
    if not isinstance(entries, list) or not entries:
        return ["move_specs: expected a non-empty list, got %r" % (entries,)]
    seen = []
    for e in entries:
        if not isinstance(e, dict) or "move_spec_version" not in e:
            problems.append("move_specs: bad entry %r" % (e,))
            continue
        version = e["move_spec_version"]
        seen.append(version)
        spec = SPECS.get(version)
        if spec is None:
            problems.append("move_specs: unknown move_spec_version %r "
                            "(this verifier knows %s)"
                            % (version, ", ".join(SPEC_ORDER)))
            continue
        if e.get("move_spec_hash") != spec.move_spec_hash:
            problems.append(
                "move_spec_hash for %s: header has %r, verifier computes %r"
                % (version, e.get("move_spec_hash"), spec.move_spec_hash))
        for key, want in (("target_relators", spec.target),
                          ("max_rank", spec.max_rank),
                          ("id_prefix", spec.id_prefix)):
            if key in e and e[key] != want:
                problems.append("move_specs[%s].%s: header has %r, "
                                "verifier expects %r"
                                % (version, key, e[key], want))
    missing = [v for v in SPEC_ORDER if v not in seen]
    if missing:
        problems.append("move_specs: missing %s" % ", ".join(missing))
    return problems
