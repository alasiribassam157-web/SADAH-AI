"""Real tools the agent uses. Every file/process operation is confined to WORKSPACE."""
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from agent.facts import answer_fact
from agent.research import lookup

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
try:
    WORKSPACE.mkdir(exist_ok=True)
except OSError:  # read-only deployments (Vercel): only the temp folder is writable
    WORKSPACE = Path(tempfile.gettempdir()) / "sadah-workspace"
    WORKSPACE.mkdir(exist_ok=True)
# Safe mode (no code or system execution) is the default on Vercel, which sets VERCEL=1
SAFE_MODE = os.getenv("NEXUS_SAFE_MODE", "1" if os.getenv("VERCEL") else "0") == "1"
_BLOCKED = re.compile(r"\b(format|shutdown|diskpart|rmdir\s+/s|rd\s+/s|del\s+/s|reg\s+delete|"
                      r"rm\s+-rf|mkfs|bcdedit|cipher\s+/w)\b", re.IGNORECASE)


@dataclass
class ToolResult:
    ok: bool
    output: str
    files: list[str] = field(default_factory=list)
    entity: str = ""  # main subject of the answer, remembered for follow-up questions
    trace: list[dict] = field(default_factory=list)  # messages between agents (agents/bus.py), shown as steps


def _safe_path(name: str) -> Path:
    """Resolve a user-supplied path and refuse anything outside the workspace."""
    path = (WORKSPACE / name.strip().strip("\"'")).resolve()
    if path != WORKSPACE and WORKSPACE not in path.parents:
        raise PermissionError(f"Path escapes workspace: {name}")
    return path


def _clip(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[:limit] + "\n... [truncated]"


class PythonExecutorTool:
    name = "PythonExecutorTool"

    def run(self, code: str, timeout: int = 10) -> ToolResult:
        if SAFE_MODE:
            return ToolResult(False, "Python execution is disabled (NEXUS_SAFE_MODE=1).")
        script = WORKSPACE / f"run_{int(time.time() * 1000)}.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", script.name], cwd=WORKSPACE,
                                  capture_output=True, text=True, timeout=timeout,
                                  encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return ToolResult(False, f"Timed out after {timeout}s", [script.name])
        out = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
        return ToolResult(proc.returncode == 0, _clip(out or "(no output)"), [script.name])


class FileManagerTool:
    name = "FileManagerTool"

    def create(self, name: str, content: str = "") -> ToolResult:
        path = _safe_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Created {path.relative_to(WORKSPACE)} ({len(content)} chars)",
                          [str(path.relative_to(WORKSPACE))])

    def read(self, name: str) -> ToolResult:
        path = _safe_path(name)
        if not path.is_file():
            return ToolResult(False, f"File not found: {name}")
        return ToolResult(True, _clip(path.read_text(encoding="utf-8", errors="replace")))

    def delete(self, name: str) -> ToolResult:
        path = _safe_path(name)
        if not path.is_file():
            return ToolResult(False, f"File not found: {name}")
        path.unlink()
        return ToolResult(True, f"Deleted {name}")

    def mkdir(self, name: str) -> ToolResult:
        path = _safe_path(name)
        path.mkdir(parents=True, exist_ok=True)
        return ToolResult(True, f"Folder ready: {path.relative_to(WORKSPACE)}")

    def list(self, folder: str = "") -> ToolResult:
        root = _safe_path(folder) if folder else WORKSPACE
        if not root.is_dir():
            return ToolResult(False, f"Folder not found: {folder}")
        items = sorted(str(p.relative_to(WORKSPACE)) + ("/" if p.is_dir() else "")
                       for p in root.rglob("*"))
        return ToolResult(True, "\n".join(items) or "(workspace is empty)")


class WebResearchTool:
    name = "WebResearchTool"
    def search(self, question: str) -> ToolResult:
        """Direct facts from Wikidata first, then a short Wikipedia answer."""
        lang = "ar" if re.search(r"[؀-ۿ]", question) else "en"
        fact = answer_fact(question, lang)
        if fact:
            return ToolResult(True, f"{fact[0]}\n\n🔗 {fact[1]}", entity=fact[2])
        try:
            found = lookup(question, lang)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            # ValueError covers non-JSON bodies (e.g. a rate-limit page).
            return ToolResult(False, f"Web request failed: {exc}")
        if not found:
            return ToolResult(False, "لم أجد إجابة لهذا السؤال." if lang == "ar"
                              else "I couldn't find an answer to that.")
        title, text, url = found
        return ToolResult(True, _clip(f"**{title}**\n\n{text}\n\n🔗 {url}"), entity=title)


class SystemTaskTool:
    name = "SystemTaskTool"

    def run(self, command: str, timeout: int = 15) -> ToolResult:
        if SAFE_MODE:
            return ToolResult(False, "System commands are disabled (NEXUS_SAFE_MODE=1).")
        if _BLOCKED.search(command):
            return ToolResult(False, f"Blocked potentially destructive command: {command}")
        try:
            proc = subprocess.run(command, shell=True, cwd=WORKSPACE, capture_output=True,
                                  text=True, timeout=timeout, errors="replace")
        except subprocess.TimeoutExpired:
            return ToolResult(False, f"Timed out after {timeout}s")
        out = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
        return ToolResult(proc.returncode == 0, _clip(out or "(no output)"))
