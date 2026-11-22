"""Runs training in a background thread and exposes live progress to the API."""
import threading
from typing import Callable

from core import lifecycle, trainer
from core.dataset_builder import BRAINS


class TrainingJob:
    def __init__(self, on_done: Callable[[str], None]):
        self.on_done = on_done  # called with the brain name after it is saved
        self.state = {"running": False, "brain": "", "history": [], "result": None, "results": [], "error": None}
        self._lock = threading.Lock()

    def start(self, brain: str = "all", size: str = "medium", epochs: int = 12) -> bool:
        with self._lock:
            if self.state["running"]:
                return False
            self.state.update(running=True, brain="", history=[], result=None, results=[], error=None)
        brains = list(BRAINS) if brain == "all" else [brain]
        threading.Thread(target=self._run, args=(brains, size, epochs), daemon=True).start()
        return True

    def _run(self, brains: list[str], size: str, epochs: int) -> None:
        try:
            for name in brains:
                self.state.update(brain=name, history=[])
                result = trainer.train(brain=name, size=size, epochs=epochs,
                                       on_epoch=lambda m: self.state["history"].append(m))
                verdict = lifecycle.review_and_promote(name, result["registry_version"])   # the gate decides
                if verdict["passed"]:
                    self.on_done(name)   # reload the live brain only when the candidate was promoted
                summary = {k: v for k, v in result.items() if k != "history"}
                summary["gate"] = {"passed": verdict["passed"], "reasons": verdict["reasons"]}
                self.state["results"].append(summary)
                self.state["result"] = summary
        except Exception as exc:  # surfaced to the UI instead of killing the thread silently
            self.state["error"] = str(exc)
        finally:
            self.state["running"] = False
