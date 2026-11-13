"""Message bus: the Supervisor asks several agents at once and gets their messages back.

Every agent runs in its own thread with a deadline, so one slow source never holds up the answer
(Vercel stops a request after about 10 seconds).  Every message is kept in the transcript.
"""
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Callable

from agents.message import FAIL, REQUEST, Message

Agent = Callable[[dict], Message]


class Bus:
    def __init__(self, deadline: float = 7.0):
        self.deadline = deadline
        self.transcript: list[Message] = []

    def post(self, msg: Message) -> Message:
        self.transcript.append(msg)
        return msg

    def ask(self, agents: dict[str, Agent], request: dict, sender: str = "Supervisor",
            primary: str = "", grace: float = 2.5) -> dict[str, Message]:
        """Send one request to every agent in parallel; agents that miss the deadline answer FAIL.

        primary: the agent whose answer we cannot do without.  Once it has replied, the others
        (the witnesses) get only `grace` more seconds, so cross-checking adds little waiting.
        """
        self.post(Message(sender, REQUEST, content=request.get("text", ""), value=" · ".join(agents)))
        pool = ThreadPoolExecutor(max_workers=max(1, len(agents)))
        start = time.time()
        futures = {name: pool.submit(_timed, agent, request) for name, agent in agents.items()}
        if primary in futures:
            wait([futures[primary]], timeout=self.deadline)
            left = self.deadline - (time.time() - start)
            wait(futures.values(), timeout=max(0.0, min(grace, left)))
        else:
            wait(futures.values(), timeout=self.deadline)
        pool.shutdown(wait=False, cancel_futures=True)   # never wait for a late agent
        replies = {}
        for name, fut in futures.items():
            if fut.done() and fut.exception() is None:
                msg = fut.result()
            else:
                why = "انتهت المهلة" if not fut.done() else f"خطأ: {fut.exception()}"
                msg = Message(name, FAIL, content=why, ms=int((time.time() - start) * 1000))
            replies[name] = self.post(msg)
        return replies

    def steps(self) -> list[dict]:
        """The conversation between the agents, in the same shape as the orchestrator's thinking steps."""
        stage = {"request": "plan", "confirm": "critic", "object": "critic"}
        status = {"fail": "warn", "object": "warn"}
        return [{"stage": stage.get(m.kind, "tool"), "title": m.line(), "detail": m.content if m.value else "",
                 "status": status.get(m.kind, "ok")} for m in self.transcript]


def _timed(agent: Agent, request: dict) -> Message:
    t0 = time.time()
    msg = agent(request)
    msg.ms = msg.ms or int((time.time() - t0) * 1000)
    return msg
