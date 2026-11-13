"""[13] Chrono agent: dates, ages, days until events (Ramadan, Eid, national days), gaps between dates,
weekdays, and today's Gregorian and Hijri date (date_math.py, live_skills.date_time; Hijri via aladhan).

Ages and gaps are recomputed a second way (birthday by birthday, ordinal day numbers) before SADAH confirms them.
"""
import re
from datetime import date, datetime

from agent import date_math, live_skills
from agent.base_agent import AgentResult, BaseAgent, Task

_NOW = re.compile(r"كم الساعة|الساعة كم|وش التاريخ|ما التاريخ|تاريخ اليوم|اليوم كم|الهجري|what time|today'?s date|"
                  r"what(?:'s| is) the date|hijri", re.I)


def check_gap(question: str, answer: str) -> bool | None:
    """«بين التاريخين N يوم»: recount with ordinal day numbers (None = not a gap question)."""
    dates = date_math._dates(question)
    shown = re.search(r"\*\*(\d+) (?:يوم|days)\*\*", answer)
    if len(dates) < 2 or not shown or "بين" not in answer and "between" not in answer:
        return None
    return abs(dates[1].toordinal() - dates[0].toordinal()) == int(shown.group(1))


def check_age(question: str, answer: str) -> bool | None:
    """«العمر: N سنة» from an exact birth date: recount by stepping through the birthdays one by one."""
    dates = date_math._dates(question)
    shown = re.search(r"(?:العمر|Age): \*\*(\d+)", answer)
    if not dates or not shown:
        return None
    today, born = datetime.now(live_skills.TZ).date(), dates[0]
    years = 0
    while _birthday(born, years + 1) <= today:   # count the birthdays one by one
        years += 1
    return years == int(shown.group(1))


def _birthday(born: date, n: int) -> date:
    try:
        return born.replace(year=born.year + n)
    except ValueError:  # born on 29 February: the birthday falls on 1 March in ordinary years
        return date(born.year + n, 3, 1)


class ChronoAgent(BaseAgent):
    name = "Chrono"
    sector = "المنطق والرياضيات"
    intents = frozenset({"datetime"})
    keywords = r"كم باقي|كم بقي|رمضان|العيد|عمري|انولدت|التاريخ|الهجري|الساعة|days until|how old|date|hijri"
    timeout = 6.0

    def can_handle(self, task: Task) -> float:
        return 0.95 if date_math.handles(task.text) or _NOW.search(task.text) else super().can_handle(task)

    def handle(self, task: Task) -> AgentResult:
        if date_math.handles(task.text):
            self.step("سَداة تحسب التاريخ", "مناسبات هجرية وميلادية، أعمار، فروق بين تاريخين")
            res = date_math.answer(task.text)
        else:
            self.step("سَداة تقرأ الوقت والتاريخ الحاليين", f"توقيت {live_skills.TZ.key}، والهجري من aladhan")
            res = live_skills.date_time(task.text)
        if not res.ok:
            return self.fail(res.output)
        checks = [c for c in (check_gap(task.text, res.output), check_age(task.text, res.output)) if c is not None]
        if checks and not all(checks):
            self.step("إعادة الحساب بطريقة ثانية لم تتطابق", status="warn", confidence=0.4)
            return self.fail("لم يتطابق الحساب الثاني؛ لن أقدّم تاريخًا غير مؤكد.")
        conf = 0.97 if checks else 0.9
        if checks:
            self.step("تحققتُ بإعادة العد بأرقام الأيام", confidence=conf)
        return self.ok(res.output, conf)
