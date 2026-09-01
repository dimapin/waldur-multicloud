"""Meta-test for the README rule: no unchecked norm, no norm-free check.

docs/contracts/README.md, ID rules 4: a requirement no test refers to is a
finding, and so is a test without an ID reference. This checks the first half
mechanically and keeps the second half honest by rejecting IDs that the
contract does not define.
"""

import re
from pathlib import Path

from waldur_multicloud import REQUIREMENTS, active_requirements
from waldur_multicloud.contract import CAPABILITIES

TESTS_DIR = Path(__file__).parent
ID_PATTERN = re.compile(r"\b(?:CON|CAP)-\d{3}\b")
#: Lines carrying this marker use a deliberately invalid ID (negative tests).
NOT_AN_ID = "# meta: not-a-contract-id"


def _referenced_ids() -> set[str]:
    found: set[str] = set()
    for path in TESTS_DIR.glob("test_*.py"):
        if path.name == Path(__file__).name:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if NOT_AN_ID in line:
                continue
            found.update(ID_PATTERN.findall(line))
    return found


def test_every_active_requirement_is_referenced_by_a_test() -> None:
    """An active CON-ID without a referencing test is an unchecked norm."""
    referenced = _referenced_ids()
    unchecked = sorted(r.id for r in active_requirements() if r.id not in referenced)
    assert not unchecked, f"active requirements without a test reference: {unchecked}"


def test_referenced_ids_exist_in_the_contract() -> None:
    """A test citing an unknown ID checks a norm that nobody decided."""
    known = set(REQUIREMENTS) | set(CAPABILITIES)
    unknown = sorted(ref for ref in _referenced_ids() if ref not in known)
    assert not unknown, f"tests reference undefined IDs: {unknown}"
