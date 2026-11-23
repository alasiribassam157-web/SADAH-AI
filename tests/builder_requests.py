"""The builder's Arabic request suite: the development requests, each with what the builder must do.

skill   landing / dashboard / shop / webapp / portfolio / blog / event / game : build a site of that kind that passes every static check,
                                              and match `expect` (spec attributes: name, business, accent, app,
                                              sections (subset), data_labels, items_n)
        ask    : build nothing and ask the one short question
        refuse : build nothing and say plainly it is not supported
"""

from tests.builder_case import SKILLS, case  # noqa: F401  (re-exported for the tests)
from tests.builder_cases_a import CASES as _A
from tests.builder_cases_b import CASES as _B
from tests.builder_cases_c import CASES as _C
from tests.builder_cases_d import CASES as _D
from tests.builder_cases_e import CASES as _E
from tests.builder_cases_f import CASES as _F

SUITE = _A + _B + _C + _D + _E + _F
