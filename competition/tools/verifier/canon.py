"""Canonical serialization and hashing (DESIGN.md §3.2, §3.3).

``instance_hash`` and ``certificate_hash`` use explicit byte templates —
fixed key order, no whitespace, ASCII only, shortest-decimal integers —
so any third-party implementation can reproduce them byte for byte
without an RFC 8785 dependency.

``move_spec_hash`` and ``manifest_hash`` use :func:`jcs`, which for the
data involved (ASCII strings, small ints, bools) coincides with RFC 8785
canonical JSON.
"""

import hashlib
import json
import re

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def sha256_str(s):
    """``"sha256:" + lowercase_hex(SHA256(utf8(s)))``."""
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


def _canon_int(n):
    """Shortest-decimal integer: ``-1`` not ``-01``, ``-0`` impossible."""
    if type(n) is not int:
        raise ValueError("canonical integers must be int, got %r" % (n,))
    return str(n)


def canon_int_list(xs):
    return "[" + ",".join(_canon_int(a) for a in xs) + "]"


def canon_relators(relators):
    return "[" + ",".join(canon_int_list(w) for w in relators) + "]"


def _canon_id(s):
    if not isinstance(s, str) or not _ID_RE.match(s):
        raise ValueError("bad canonical identifier: %r" % (s,))
    return s


def instance_canon(challenge_id, generators, initial_relators,
                   target_relators, move_spec_version, move_spec_hash):
    """Exact byte template of DESIGN.md §3.2 (fixed key order)."""
    gens = "[" + ",".join('"%s"' % _canon_id(g) for g in generators) + "]"
    return ('{"challenge_id":"%s","generators":%s,'
            '"initial_relators":%s,'
            '"target_relators":%s,'
            '"move_spec_version":"%s","move_spec_hash":"%s"}') % (
        _canon_id(challenge_id), gens,
        canon_relators(initial_relators),
        canon_relators(target_relators),
        _canon_id(move_spec_version), move_spec_hash)


def instance_hash(challenge_id, generators, initial_relators,
                  target_relators, move_spec_version, move_spec_hash):
    return sha256_str(instance_canon(
        challenge_id, generators, initial_relators, target_relators,
        move_spec_version, move_spec_hash))


def certificate_canon(challenge_id, move_spec_version, moves):
    """Exact byte template of DESIGN.md §3.2 for certificates."""
    return ('{"challenge_id":"%s","move_spec_version":"%s","moves":%s}'
            % (_canon_id(challenge_id), _canon_id(move_spec_version),
               canon_int_list(moves)))


def certificate_hash(challenge_id, move_spec_version, moves):
    return sha256_str(certificate_canon(challenge_id, move_spec_version, moves))


def jcs(obj):
    """Canonical JSON for plain ASCII/int/bool data (= RFC 8785 there)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def move_spec_hash(move_table):
    """``sha256(JCS of the frozen 14-row move table)`` (DESIGN.md §3.3)."""
    return sha256_str(jcs(list(move_table)))


def manifest_hash(instance_hashes):
    """``sha256(JCS of sorted list of instance_hash)`` (DESIGN.md §3.3)."""
    return sha256_str(jcs(sorted(instance_hashes)))
