"""Programming skill: the coder brain picks the task, the knowledge base supplies verified code."""
import re

from agent import lexicon
from agent.code_kb import detect_language, render
from agent.tools import ToolResult
from core.inference import BrainInference

CONFIDENCE_FLOOR = 0.45
WEAK_FLOOR = 0.15      # the brain may hesitate on dialect («سوي لي دالة…») — the roots then confirm it


class CoderSkill:
    def __init__(self):
        self.brain = BrainInference("coder")

    def answer(self, question: str) -> tuple[ToolResult, str, float]:
        """Return (result, task, confidence)."""
        ui_lang = "ar" if re.search(r"[؀-ۿ]", question) else "en"
        if not self.brain.ready and not self.brain.reload():
            return ToolResult(False, "Coder brain is not trained yet."), "", 0.0
        task, conf, _ = self.brain.predict(question)
        lang = detect_language(question) or "python"
        if conf < CONFIDENCE_FLOOR:   # confirm or replace the guess by matching the 45 tasks' own words
            if conf >= WEAK_FLOOR and lexicon.supports(question, task):
                conf = CONFIDENCE_FLOOR
            elif found := lexicon.task_by_root(question):
                task, conf = found, max(conf, CONFIDENCE_FLOOR)
        if conf < CONFIDENCE_FLOOR:
            hint = ("ما فهمت المهمة البرمجية بالضبط. جرّب مثلاً: «كيف أعكس نص في Python» أو «حلقة for في Java»."
                    if ui_lang == "ar" else
                    "I'm not sure which programming task you mean. Try «how to reverse a string in Python».")
            return ToolResult(False, hint), task, conf
        return ToolResult(True, render(task, lang, ui_lang, conf), entity=lang), task, conf
"""Programming skill: the coder brain picks the task, the knowledge base supplies verified code."""
import re

from agent.code_kb import detect_language, render
from agent.tools import ToolResult
from core.inference import BrainInference

CONFIDENCE_FLOOR = 0.45


class CoderSkill:
    def __init__(self):
        self.brain = BrainInference("coder")

    def answer(self, question: str) -> tuple[ToolResult, str, float]:
        """Return (result, task, confidence)."""
        ui_lang = "ar" if re.search(r"[؀-ۿ]", question) else "en"
        if not self.brain.ready and not self.brain.reload():
            return ToolResult(False, "Coder brain is not trained yet."), "", 0.0
        task, conf, _ = self.brain.predict(question)
        lang = detect_language(question) or "python"
        if conf < CONFIDENCE_FLOOR:
            hint = ("ما فهمت المهمة البرمجية بالضبط. جرّب مثلاً: «كيف أعكس نص في Python» أو «حلقة for في Java»."
                    if ui_lang == "ar" else
                    "I'm not sure which programming task you mean. Try «how to reverse a string in Python».")
            return ToolResult(False, hint), task, conf
        return ToolResult(True, render(task, lang, ui_lang, conf), entity=lang), task, conf
