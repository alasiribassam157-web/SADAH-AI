"""[14] Forex agent: currency conversion with live rates (open.er-api.com through live_skills.currency).

Check: currencies pegged to the dollar (riyal, dirham, Qatari riyal …) must match their official peg;
any other pair is checked by fetching the reverse rate, since a→b × b→a must be ≈ 1.
"""
import re

import httpx

from agent import live_skills
from agent.base_agent import AgentResult, BaseAgent, Task

PEGS = {"USD": 1.0, "SAR": 3.75, "AED": 3.6725, "QAR": 3.64, "BHD": 0.376, "OMR": 0.3845, "JOD": 0.709}
TOLERANCE = 0.01   # 1 %: rates move during the day and providers round


def rate_check(src: str, dst: str) -> tuple[bool | None, str]:
    """(agrees?, how) — None when no independent reference could be reached."""
    rates = live_skills._RATES.get(src, (0, {}))[1]
    if dst not in rates:
        return None, ""
    rate = rates[dst]
    if src in PEGS and dst in PEGS:
        peg = PEGS[dst] / PEGS[src]
        return abs(rate - peg) / peg <= TOLERANCE, f"طابق السعر الربطَ الرسمي ({peg:.4f})"
    try:
        back = httpx.get(f"https://open.er-api.com/v6/latest/{dst}", timeout=5, headers=live_skills.HEADERS).json()
        reverse = back["rates"][src]
    except (httpx.HTTPError, ValueError, KeyError):
        return None, ""
    return abs(rate * reverse - 1) <= TOLERANCE, f"السعر العكسي يؤكد السعر (×{rate * reverse:.4f})"


class ForexAgent(BaseAgent):
    name = "Forex"
    sector = "البيانات الحية"
    intents = frozenset({"currency"})
    keywords = r"دولار|ريال|يورو|درهم|دينار|جنيه|ين|استرليني|dollar|riyal|euro|dirham|dinar|pound|yen|usd|eur|sar"
    timeout = 8.0

    def can_handle(self, task: Task) -> float:
        return 0.9 if live_skills.find_currencies(task.text) else super().can_handle(task)

    def handle(self, task: Task) -> AgentResult:
        codes = list(dict.fromkeys(live_skills.find_currencies(task.text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩",
                                                                                               "0123456789")))))
        self.step("سَداة تجلب سعر الصرف الحي", " → ".join(codes) or "عملة غير محددة")
        res = live_skills.currency(task.text)
        if not res.ok:
            return self.fail(res.output)
        if len(codes) >= 2:
            src, dst = self._order(task.text, codes)
        else:   # one currency named: live_skills converts it to riyals (or riyals to dollars)
            src, dst = codes[0], ("SAR" if codes[0] != "SAR" else "USD")
        agreed, how = rate_check(src, dst)
        if agreed is False:
            self.step("السعر لم يطابق المرجع المستقل", f"{src}→{dst}", "warn", 0.4)
            return self.fail("سعر الصرف لم يطابق المرجع المستقل؛ لن أقدّم رقمًا غير مؤكد.")
        conf = 0.95 if agreed else 0.85
        if agreed:
            self.step(f"تحققتُ: {how}", confidence=conf)
        return self.ok(res.output, conf, ["https://www.exchangerate-api.com"], {"src": src, "dst": dst})

    @staticmethod
    def _order(text: str, codes: list[str]) -> tuple[str, str]:
        """Same rule as live_skills.currency: the currency right after the amount is the source."""
        text = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        amount = re.search(r"\d+(?:[.,]\d+)?", text)
        found = live_skills._find(text)
        if amount:
            after = [code for start, _, code in found if start >= amount.end()]
            if after:
                return after[0], next(c for c in codes if c != after[0])
        return codes[0], codes[1]
