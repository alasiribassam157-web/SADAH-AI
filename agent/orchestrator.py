"""NEXUS agent loop: Remember → Perceive → Critic → Plan → Act → Verify → Answer."""
import re
import time

from agent import composer, critic
from agent.chat_replies import chat_reply
from agent.companion import Companion
from agent.dispatch import TOOL_NAMES, Dispatcher
from agent.memory import ConversationMemory
from agent.planner import make_plan
from core.inference import BrainInference

FORMATTED_TOOLS = ("web", "code", "weather", "currency", "datetime", "units", "prayer", "translate", "math",
                   "compare")  # already markdown


class NexusAgent:
    def __init__(self):
        self.brain = BrainInference("router")
        self.tools = Dispatcher()
        self.memory = ConversationMemory()
        self.companion = Companion()

    @property
    def brains(self) -> dict[str, BrainInference]:
        return {"router": self.brain, "coder": self.tools.coder.brain}

    def handle(self, message: str, allow_exec: bool = False, session: str = "") -> dict:
        """Answer a message; compound questions («…وكم عدد سكانها») are split and answered part by part."""
        parts = composer.split_compound(message)
        if len(parts) == 1:
            result = self._handle_one(message, allow_exec, session)
            self.companion.note(session, message, result["answer"])
            return result
        session = session or f"compound-{id(parts)}"  # follow-up parts need memory to resolve «سكانها»
        results = [self._handle_one(part, allow_exec, session) for part in parts]
        merged = dict(results[0])
        merged["answer"] = "\n\n".join(r["answer"] for r in results)
        merged["steps"] = [s for r in results for s in r["steps"]]
        merged["ms"] = sum(r["ms"] for r in results)
        return merged

    def _handle_one(self, message: str, allow_exec: bool = False, session: str = "") -> dict:
        """allow_exec: run real Python/system commands (only for the developer's own machine)."""
        t0 = time.time()
        lang = "ar" if re.search(r"[؀-ۿ]", message) else "en"
        steps, neural = [], ""  # neural = the brain's own answer before the critic steps in

        def step(stage: str, title: str, detail: str = "", status: str = "ok"):
            steps.append({"stage": stage, "title": title, "detail": detail, "status": status})

        def done(answer: str, intent: str, conf: float, files=()) -> dict:
            return {"steps": steps, "answer": answer, "files": list(files), "intent": intent, "neural_intent": neural,
                    "confidence": round(conf, 3), "ms": int((time.time() - t0) * 1000)}

        # 0. Conversation memory: "وكم عدد سكانها؟" -> "وكم عدد سكان اليابان"
        resolved = self.memory.resolve(session, message)
        if resolved != message:
            step("plan", "Follow-up resolved", f"{message} → {resolved}")
            message = resolved

        # 1. Perceive — neural intent classification
        if not self.brain.ready and not self.brain.reload():
            step("plan", "Brain not trained", "Train the router brain first.", "error")
            return done("⚠️ Model not trained yet.", "unknown", 0.0)
        intent, conf, dist = self.brain.predict(message)
        neural = intent
        step("plan", f"Intent: {intent} ({conf:.0%})",
             " · ".join(f"{k} {v:.0%}" for k, v in sorted(dist.items(), key=lambda kv: -kv[1])[:4]))

        # 1b. Conversation: the person talks about themselves, their mood, or just chats
        talk = self.companion.respond(session, message, lang)
        if talk:
            step("result", "Conversation", "Personal reply (name, mood and the last 5 messages are remembered).")
            return done(talk, "chat", conf)

        # 2. Critic reviews the classification itself
        intent, note = critic.review_intent(message, intent, conf)
        step("critic", "Intent review", note)
        if intent == "chat":
            step("result", "Direct reply", "No tool needed.")
            return done(chat_reply(message, lang), intent, conf)

        # 3. Plan the tool call and let the critic approve / repair it
        plan = make_plan(message, intent)
        step("tool", f"{TOOL_NAMES[plan['tool']]}.{plan['action']}", _preview(plan["args"]))
        approved, plan, notes = critic.review_plan(plan)
        step("critic", "Pre-execution check", "\n".join(notes), "ok" if approved else "error")
        if not approved:
            return done("❌ " + notes[-1], intent, conf)

        # 4. Act, then verify; one self-correcting retry for Python runtime errors
        result = self.tools.execute(plan, allow_exec)
        steps.extend(result.trace)  # the agents' conversation (request → answers → critic)
        valid, verdict = critic.review_result(plan, result)
        if not valid and allow_exec and plan["tool"] == "python" and "Traceback" in result.output:
            step("critic", "Self-correction", "Runtime error — retrying with standard imports.", "warn")
            plan["args"]["code"] = "from math import *\nimport statistics, json, re\n" + plan["args"]["code"]
            result = self.tools.execute(plan, allow_exec)
            valid, verdict = critic.review_result(plan, result)
        if plan["tool"] == "code":
            task, task_conf = self.tools.last_code_task
            step("tool", f"Coder brain: {task} ({task_conf:.0%})")
        step("critic", "Post-execution verification", verdict, "ok" if valid else "warn")
        self.memory.remember(session, result.entity)

        if plan["tool"] in FORMATTED_TOOLS or not result.ok:
            answer = result.output
        elif "\n" not in result.output and len(result.output) < 160:
            answer = f"**{result.output}**"
        else:
            answer = f"```\n{result.output}\n```"
        step("result", "Final answer", "Verified ✓" if valid else "Unverified — review output",
             "ok" if valid else "warn")
        return done(answer, intent, conf, result.files)


def _preview(args: dict) -> str:
    return "\n".join(f"{k}: {str(v)[:300]}" for k, v in args.items())
