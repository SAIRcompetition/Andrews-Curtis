"""Verifier + frozen-data test suite.

Run from the repo root:  python3 -m unittest discover -s tests -t .

The reference verifier package lives inside the public tree
(``competition/tools/verifier``); put it on ``sys.path`` before any test
module imports ``acms_verify``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "competition" / "tools" / "verifier"))
