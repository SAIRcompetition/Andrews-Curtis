"""ACMS reference verifier — Python, standard library only (D-10).

The same ``acms_verify`` sources run server-side and ship in the public
release package; there is no port.  See DESIGN.md §4 for the frozen
semantics.

Two frozen move specs are implemented, one per Discovery problem:
``ac-r2-v1`` (:mod:`acms_verify.core`) and ``sac-r8-v1``
(:mod:`acms_verify.stable_core`).  :mod:`acms_verify.specs` is the
registry every dispatch goes through; the top-level ``MOVE_TABLE``,
``NUM_MOVES``, ``apply_move`` and ``verify`` names re-exported below
remain the ``ac-r2-v1`` ones, unchanged.
"""

__version__ = "0.2.0"

from .core import (  # noqa: F401
    GENS,
    INVERSE_MOVE,
    MOVE_SPEC_VERSION,
    MOVE_TABLE,
    NUM_MOVES,
    apply_move,
    free_reduce,
    invert,
    verify,
)
from . import specs, stable_core  # noqa: F401
from .specs import (  # noqa: F401
    SPECS,
    SPEC_ORDER,
    check_move_specs,
    move_spec_hashes,
    verify_challenge,
)
from .canon import (  # noqa: F401
    certificate_canon,
    certificate_hash,
    instance_canon,
    instance_hash,
    jcs,
    manifest_hash,
    move_spec_hash,
)
from .submission import (  # noqa: F401
    DEFAULT_STRUCTURAL_LIMITS,
    FORBIDDEN_RESULT_KEYS,
    MAX_BODY_BYTES,
    MAX_NOTES_CHARS,
    MAX_SOLUTIONS,
    build_challenge_index,
    process_submission,
)
