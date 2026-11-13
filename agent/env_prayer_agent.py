"""[16] Environment & prayer agent: weather (Open-Meteo, live_skills.weather) and prayer times
(Open-Meteo geocoding + aladhan, prayer.py).

Checks: the five prayers (and sunrise) must come in their natural order through the day, and the
temperature must be physically plausible.
"""
import re

from agent import live_skills, prayer
from agent.base_agent import AgentResult, BaseAgent, Task

_PRAYER = re.compile(r"صلا|صلاة|صلاه|أذان|اذان|الفجر|الظهر|العصر|المغرب|العشاء|prayer|fajr|dhuhr|asr|maghrib|isha", re.I)
_CLOCK = re.compile(r"(\d{1,2}):(\d{2})\s*(ص|م|AM|PM)")


def in_order(text: str) -> bool | None:
    """True when every listed time is later than the one before it (None if fewer than five times)."""
    minutes = []
    for h, m, half in _CLOCK.findall(text):
        hour = int(h) % 12 + (12 if half in ("م", "PM") else 0)
        minutes.append(hour * 60 + int(m))
    if len(minutes) < 5:
        return None
    return all(a < b for a, b in zip(minutes, minutes[1:]))


def plausible(text: str) -> bool | None:
    temps = [float(t) for t in re.findall(r"(-?\d+(?:\.\d+)?)\s*°", text)]
    return all(-70 <= t <= 60 for t in temps) if temps else None


class EnvPrayerAgent(BaseAgent):
    name = "EnvPrayer"
    sector = "البيانات الحية"
    intents = frozenset({"weather", "prayer"})
    keywords = r"طقس|الجو|حرارة|مطر|weather|temperature|" + _PRAYER.pattern
    timeout = 8.0

    def handle(self, task: Task) -> AgentResult:
        asks_prayer = task.intent == "prayer" or (task.intent != "weather" and _PRAYER.search(task.text))
        if asks_prayer:
            self.step("سَداة تجلب مواقيت الصلاة", "تحديد المدينة ثم aladhan بطريقة الحساب المعتمدة في بلدها")
            res = prayer.prayer_times(task.text)
            check, how = in_order(res.output) if res.ok else None, "المواقيت مرتبة ترتيبًا صحيحًا خلال اليوم"
            source = "https://aladhan.com"
        else:
            self.step("سَداة تجلب حالة الطقس", "تحديد المدينة ثم Open-Meteo")
            res = live_skills.weather(task.text)
            check, how = plausible(res.output) if res.ok else None, "درجات الحرارة ضمن المدى الفيزيائي المعقول"
            source = "https://open-meteo.com"
        if not res.ok:
            return self.fail(res.output)
        if check is False:
            self.step("البيانات لم تجتز فحص المعقولية", status="warn", confidence=0.3)
            return self.fail("البيانات الواردة غير منطقية؛ لن أعرضها.")
        conf = 0.93 if check else 0.85
        if check:
            self.step(f"تحققتُ: {how}", confidence=conf)
        sources = re.findall(r"🔗 (\S+)", res.output) or [source]
        return self.ok(res.output, conf, sources, {"kind": "prayer" if asks_prayer else "weather"}, entity=res.entity)
