"""[12] Units agent: length, mass, volume, speed, data, area and temperature (units.py).

The converted value is checked by converting it back to the original unit.
"""
import math
import re

from agent import units
from agent.base_agent import AgentResult, BaseAgent, Task

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def round_trip(question: str, answer: str) -> bool | None:
    """Convert the answer back; True when it returns to the original amount (None = can't check)."""
    text = question.translate(_DIGITS)
    num = units._NUM.search(text)
    found = list(dict.fromkeys(u for _, u in units._find_units(text)))
    shown = re.findall(r"=\s*(-?[\d,]+(?:\.\d+)?)", answer)
    if not num or len(found) < 2 or not shown:
        return None
    value = float(num.group().replace(",", "."))
    after = [u for pos, u in units._find_units(text) if pos >= num.end()]
    src = after[0] if after else found[0]
    dst = next(u for u in found if u != src)
    result = float(shown[0].replace(",", ""))
    if units.UNITS[src][0] == "temp":
        back = units._to_temp(result, dst, src)
    else:
        back = result * units.UNITS[dst][1] / units.UNITS[src][1]
    return math.isclose(back, value, rel_tol=1e-3, abs_tol=1e-3)


class UnitsAgent(BaseAgent):
    name = "Units"
    sector = "المنطق والرياضيات"
    intents = frozenset({"units"})
    keywords = r"حول|تحويل|كم .* في|convert|to (?:km|miles|kg|pounds|cm|inches|feet|celsius|fahrenheit)"
    timeout = 2.0

    def can_handle(self, task: Task) -> float:
        return 0.95 if units.is_conversion(task.text) else super().can_handle(task)

    def handle(self, task: Task) -> AgentResult:
        self.step("سَداة تحوّل الوحدات", "جداول الطول والكتلة والحجم والسرعة والبيانات والمساحة والحرارة")
        res = units.convert(task.text)
        if not res.ok:
            return self.fail(res.output)
        back = round_trip(task.text, res.output)
        if back is False:
            self.step("التحويل العكسي لم يرجع للقيمة الأصلية", status="warn", confidence=0.4)
            return self.fail("لم يتطابق التحويل العكسي؛ لن أقدّم رقمًا غير مؤكد.")
        conf = 0.97 if back else 0.9
        if back:
            self.step("تحققتُ بالتحويل العكسي إلى الوحدة الأصلية", confidence=conf)
        return self.ok(res.output, conf, data={"round_trip": back})
