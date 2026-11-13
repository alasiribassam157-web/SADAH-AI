"""[15] Markets agent: live gold and silver (gold-api.com) and crypto (CoinGecko) prices via markets.py.

Quotes only, never advice.  Check: each price must sit in a sane range, and the per-gram riyal prices
must follow from the ounce price (ounce × 3.75 ÷ 31.1035 × karat ÷ 24).
"""
import re

from agent import markets
from agent.base_agent import AgentResult, BaseAgent, Task

SANE_USD = {"الذهب": (300, 20_000), "Gold": (300, 20_000), "الفضة": (3, 500), "Silver": (3, 500)}


def consistent(text: str) -> tuple[bool | None, str]:
    """Recompute the karat prices from the ounce price shown in the answer."""
    ounce = re.search(r"(?:سعر (\S+) الآن:\*\*|\*\*(\w+) now:\*\* \$)\s*([\d,]+\.\d+)", text)
    if not ounce:
        return None, ""
    name, usd = ounce.group(1) or ounce.group(2), float(ounce.group(3).replace(",", ""))
    low, high = SANE_USD.get(name, (0, float("inf")))
    if not low <= usd <= high:
        return False, f"سعر الأونصة ({usd:,.2f}$) خارج النطاق المعقول"
    for karat, shown in re.findall(r"(?:عيار |• )(\d{2})K?: \*\*([\d,]+\.\d+)", text):
        expected = usd * markets.USD_SAR / markets.OUNCE_G * int(karat) / 24
        if abs(expected - float(shown.replace(",", ""))) > 0.011:   # shown rounded to 2 decimals
            return False, f"سعر عيار {karat} لا يطابق سعر الأونصة"
    return True, "أعدتُ حساب أسعار الجرام من سعر الأونصة فتطابقت"


class MarketsAgent(BaseAgent):
    name = "Markets"
    sector = "البيانات الحية"
    intents = frozenset({"currency"})
    keywords = r"ذهب|فضة|بيتكوين|بتكوين|إيثيريوم|كريبتو|عملات رقمية|gold|silver|bitcoin|ethereum|crypto"
    timeout = 8.0

    def can_handle(self, task: Task) -> float:
        return 0.95 if markets.asks_price(task.text) else super().can_handle(task)

    def handle(self, task: Task) -> AgentResult:
        self.step("سَداة تجلب أسعار السوق الحية", "الذهب والفضة من gold-api، والعملات الرقمية من CoinGecko")
        res = markets.quote(task.text)
        if not res.ok:
            return self.fail(res.output)
        agreed, how = consistent(res.output)
        if agreed is False:
            self.step(how, status="warn", confidence=0.3)
            return self.fail(f"{how}؛ لن أقدّم سعرًا غير منطقي.")
        conf = 0.93 if agreed else 0.85
        if agreed:
            self.step(f"تحققتُ: {how}", confidence=conf)
        links = re.findall(r"🔗 (\S+)", res.output)
        return self.ok(res.output, conf, links, {"kind": "quote"})
