"""SADAH 2.0 — the central message bus the 20 micro-agents talk through.

route()        rank the registered agents for a task (intent + keywords)
ask()          one agent, with its own deadline
broadcast()    several agents in parallel; a primary may cut the witnesses' waiting short
first_success  try agents in order until one succeeds (the critic's fallback path)
Every message is kept in the transcript and turned into thinking steps for the answer.
"""
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field

from agent.base_agent import AgentResult, BaseAgent, Task, TraceStep

REQUEST, REPLY, TIMEOUT, NOTE = "request", "reply", "timeout", "note"
_STAGE = {REQUEST: "plan", REPLY: "tool", TIMEOUT: "tool", NOTE: "critic"}


@dataclass
class Envelope:
    sender: str
    recipient: str
    kind: str                        # request / reply / timeout / note
    content: str = ""
    result: AgentResult | None = None
    ts: float = field(default_factory=time.time)


class MessageBus:
    def __init__(self, deadline: float = 9.0):
        self.deadline = deadline     # Vercel stops a request after about 10 seconds
        self.agents: dict[str, BaseAgent] = {}
        self.transcript: list[Envelope] = []

    # --- registry
    def register(self, *agents: BaseAgent) -> "MessageBus":
        for agent in agents:
            self.agents[agent.name] = agent
        return self

    def get(self, name: str) -> BaseAgent | None:
        return self.agents.get(name)

    def route(self, task: Task, limit: int = 3, floor: float = 0.3) -> list[str]:
        """Best-fitting agents first; only those scoring at least `floor`."""
        scored = sorted(((a.can_handle(task), n) for n, a in self.agents.items()), reverse=True)
        return [n for s, n in scored if s >= floor][:limit]

    # --- messaging
    def note(self, sender: str, content: str):
        """A remark that is not an answer (the critic's verdict, the supervisor's plan)."""
        self.transcript.append(Envelope(sender, "*", NOTE, content))

    def ask(self, name: str, task: Task, sender: str = "Supervisor") -> AgentResult:
        return self.broadcast([name], task, sender)[name]

    def broadcast(self, names: list[str], task: Task, sender: str = "Supervisor",
                  primary: str = "", grace: float = 2.5) -> dict[str, AgentResult]:
        """Run the agents in parallel.  Late or unknown agents come back as failures, never block."""
        known = [n for n in names if n in self.agents]
        for n in names:
            self.transcript.append(Envelope(sender, n, REQUEST, task.text))
        results: dict[str, AgentResult] = {n: AgentResult(n, False, "وكيل غير مسجّل") for n in names
                                           if n not in self.agents}
        if not known:
            return results
        start = time.time()
        pool = ThreadPoolExecutor(max_workers=len(known))
        futures = {n: pool.submit(self.agents[n].run, task) for n in known}
        self._wait(futures, start, primary, grace)
        pool.shutdown(wait=False, cancel_futures=True)
        for n, fut in futures.items():
            if fut.done():
                res, kind = fut.result(), REPLY   # run() never raises
            else:
                res, kind = AgentResult(n, False, "انتهت المهلة قبل أن يرد الوكيل",
                                        ms=int((time.time() - start) * 1000)), TIMEOUT
            results[n] = res
            self.transcript.append(Envelope(n, sender, kind, res.answer[:200], res))
        return results

    def _wait(self, futures: dict, start: float, primary: str, grace: float):
        """Each agent gets its own deadline; once the primary replies, the others get only `grace` more."""
        due = {n: start + min(self.deadline, self.agents[n].timeout) for n in futures}
        cut = None
        while True:
            now = time.time()
            if cut is None and primary in futures and futures[primary].done():
                cut = now + grace
                due = {n: min(d, cut) for n, d in due.items()}
            pending = [n for n, f in futures.items() if not f.done() and now < due[n]]
            if not pending:
                break
            wait([futures[n] for n in pending], timeout=min(due[n] for n in pending) - now,
                 return_when=FIRST_COMPLETED)

    def first_success(self, names: list[str], task: Task, sender: str = "Critic",
                      min_confidence: float = 0.5) -> AgentResult | None:
        """Ask one agent after another until an answer is good enough; None if nobody manages."""
        for n in names:
            res = self.ask(n, task, sender)
            if res.ok and res.confidence >= min_confidence:
                return res
            self.note(sender, f"{n} لم يقدّم إجابة كافية، أجرّب وكيلًا بديلًا")
        return None

    # --- output
    def steps(self) -> list[dict]:
        """The whole conversation, as thinking steps: requests, each agent's own steps, replies, notes."""
        out = []
        for env in self.transcript:
            if env.kind == REQUEST:
                out.append({"stage": "plan", "title": f"{env.sender} → {env.recipient}", "detail": env.content,
                            "status": "ok"})
            elif env.kind == NOTE:
                out.append({"stage": "critic", "title": env.sender, "detail": env.content, "status": "ok"})
            else:
                out.extend(s.as_step() for s in env.result.trace)
                if env.kind == TIMEOUT:
                    out.append(TraceStep(env.sender, env.content, status="warn", ms=env.result.ms).as_step())
        return out

    def sources(self) -> list[str]:
        seen = []
        for env in self.transcript:
            for src in (env.result.sources if env.result and env.result.ok else []):
                if src not in seen:
                    seen.append(src)
        return seen

    def reset(self):
        self.transcript = []
