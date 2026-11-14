"""SADAH 2.0 orchestrator: 20 micro-agents on one message bus answer every message.

Remember (companion) → Perceive (router brain) → Critic reviews the intent → Supervisor plans
primary + witnesses + fallback → agents answer in parallel → Critic verifies and cross-checks →
Companion writes the reply in SADAH's voice.  The response keeps the same shape as before.
"""
import time

from agent import composer
from agent.base_agent import AgentResult, Task
from agent.chat_replies import chat_reply
from agent.chrono_agent import ChronoAgent
from agent.code_architect_agent import CodeArchitectAgent
from agent.code_synthesizer_agent import CodeSynthesizerAgent, is_multi_step
from agent.coder import CoderSkill
from agent.companion_agent import NO_ANSWER, CompanionAgent, speak_as_sadah
from agent.critic_security_agent import CriticSecurityAgent
from agent.env_prayer_agent import EnvPrayerAgent
from agent.forex_agent import ForexAgent
from agent.local_kb_agent import LocalKBAgent
from agent.markets_agent import MarketsAgent
from agent.message_bus import MessageBus
from agent.numeric_math_agent import NumericMathAgent
from agent.open_web_agent import OpenWebAgent
from agent.sandbox_agent import SandboxAgent
from agent.stylist_agent import StylistAgent
from agent.supervisor_agent import SupervisorAgent
from agent.symbolic_math_agent import SymbolicMathAgent
from agent.synthesis_agent import SynthesisAgent
from agent.tools import _clip
from agent.translation_agent import TranslationAgent
from agent.units_agent import UnitsAgent
from agent.wiki_agent import WikiAgent
from agent.wikidata_agent import WikidataAgent


class NexusAgent:
    """Kept under its old name: app.py, the tests and the developer tools import it."""

    def __init__(self):
        coder, local, wiki = CoderSkill(), LocalKBAgent(), WikiAgent()
        self.companion, self.supervisor, self.critic = CompanionAgent(), SupervisorAgent(), CriticSecurityAgent()
        agents = [self.companion, self.supervisor, self.critic, local, wiki, WikidataAgent(), OpenWebAgent(),
                  TranslationAgent(), SynthesisAgent(local, wiki), StylistAgent(), SymbolicMathAgent(),
                  NumericMathAgent(), UnitsAgent(), ChronoAgent(), ForexAgent(), MarketsAgent(), EnvPrayerAgent(),
                  CodeArchitectAgent(coder), CodeSynthesizerAgent(coder), SandboxAgent()]
        self.registry = {a.name: a for a in agents}
        self.brain, self.coder = self.supervisor.brain, coder

    @property
    def brains(self) -> dict:
        return {"router": self.brain, "coder": self.coder.brain}

    def handle(self, message: str, allow_exec: bool = False, session: str = "") -> dict:
        """Compound questions («…وكم عدد سكانها») are answered part by part, sharing the conversation memory."""
        parts = composer.split_compound(message)
        if len(parts) > 1:
            session = session or f"compound-{id(parts)}"
        results = [self._one(part, allow_exec, session) for part in parts]
        merged = dict(results[0])
        if len(results) > 1:
            merged["answer"] = "\n\n".join(r["answer"] for r in results)
            merged["steps"] = [s for r in results for s in r["steps"]]
            merged["ms"] = sum(r["ms"] for r in results)
        self.companion.talk.note(session, message, merged["answer"])
        return merged

    def _one(self, message: str, allow_exec: bool, session: str) -> dict:
        t0, steps = time.time(), []
        step = (lambda stage, title, detail="", status="ok": steps.append(
            {"stage": stage, "title": title, "detail": detail, "status": status}))
        task = self.companion.resolve(Task(message, session=session, allow_exec=allow_exec))
        if task.context.get("followup"):
            step("plan", "سَداة فهمت السؤال من سياق المحادثة", task.context["followup"])

        def done(answer: str, intent: str, conf: float, files=()) -> dict:
            return {"steps": steps, "answer": _clip(answer), "files": list(files), "intent": intent,
                    "neural_intent": neural, "confidence": round(conf, 3), "ms": int((time.time() - t0) * 1000)}

        neural, conf, dist = self.supervisor.perceive(task.text)
        top = " · ".join(f"{k} {v:.0%}" for k, v in sorted(dist.items(), key=lambda kv: -kv[1])[:4])
        step("plan", f"العقل الموجّه: {neural} ({conf:.0%})", top)
        talk = self.companion.talk.respond(session, task.text, task.lang)
        if talk:
            step("result", "سَداة تردّ بشكل شخصي", "تتذكر الاسم والمزاج وآخر خمس رسائل")
            return done(speak_as_sadah(talk, task.lang), "chat", conf)
        intent, note = self.critic.review_intent(task.text, neural, conf)
        step("critic", "الناقد راجع نوع السؤال", note)
        if intent == "chat":
            step("result", "رد مباشر", "لا يحتاج أداة")
            return done(speak_as_sadah(chat_reply(task.text, task.lang), task.lang), intent, conf)
        task.intent = intent
        plan = self._plan(task)
        allowed, why = self.critic.allowed(plan, task)
        if not allowed:
            step("critic", "الناقد أوقف التنفيذ", why, "error")
            return done(why, intent, conf)
        bus = MessageBus()
        bus.agents = self.registry
        best, replies = self.supervisor.execute(bus, task, plan)
        steps.extend(bus.steps())
        return done(self._reply(task, plan, best, replies, step), intent, conf, best.data.get("files", ()))

    def _plan(self, task: Task) -> dict:
        plan = self.supervisor.route(task.text, task.intent)
        if task.intent == "python" and task.allow_exec and "```" in task.text:   # the developer's own code
            plan.update(primary="Sandbox", witnesses=[], fallback=[])
        elif task.intent == "code" and is_multi_step(task.text):
            plan.update(primary="CodeSynthesizer", witnesses=[], fallback=["CodeArchitect"])
        return plan

    def _reply(self, task: Task, plan: dict, best: AgentResult, replies: dict, step) -> str:
        valid, verdict = self.critic.verify(best)
        step("critic", "تحقق الناقد بعد التنفيذ", verdict, "ok" if valid else "warn")
        self.companion.memory.remember(task.session, best.entity)
        if not best.ok:
            step("result", "لا توجد إجابة موثوقة", best.answer[:200], "warn")
            return NO_ANSWER[task.lang] if task.intent == "web" else best.answer
        badge, extra = "", ()
        witnesses = [replies[w] for w in plan["witnesses"] if w in replies and w != best.agent]
        if witnesses:
            status, badge = self.critic.cross_check(best, witnesses, task.lang)
            step("critic", f"مقارنة المصادر: {status}", badge.replace("*", ""), "warn" if status == "conflict" else "ok")
            extra = [s for w in witnesses for s in w.sources] if status != "single" else ()
        step("result", "الإجابة النهائية", f"{best.agent} · ثقة {best.confidence:.0%}", "ok" if valid else "warn")
        return self.companion.compose(task, [best], badge, extra)
