"""[19] Sandbox agent: files (confined to workspace/, as before, for everyone) and — only on the
developer's own machine (localhost:8000, execution allowed, NEXUS_SAFE_MODE off) — Python and system tasks.

Before anything runs, the critic reads the code (AST) or the command.
"""
from agent import planner
from agent.base_agent import AgentResult, BaseAgent, Task
from agent.critic_security_agent import CriticSecurityAgent, scan_code
from agent.tools import SAFE_MODE, FileManagerTool, PythonExecutorTool, SystemTaskTool

LOCAL_ONLY = {"ar": "تنفيذ الكود والأوامر والملفات متاح على جهاز المطوّر فقط (localhost:8000)، وليس على الموقع العام.",
              "en": "Running code, commands and files is available only on the developer's machine (localhost:8000)."}
# For the developer's own scripts the critic still blocks the calls that can wreck a machine.
HARD_BLOCK = ("استيراد ممنوع: subprocess", "استيراد ممنوع: shutil", "استيراد ممنوع: ctypes", "دالة ممنوعة: eval()",
              "دالة ممنوعة: exec()", "دالة ممنوعة: __import__()")


class SandboxAgent(BaseAgent):
    name = "Sandbox"
    sector = "البرمجة والأمان"
    intents = frozenset({"file", "system"})
    keywords = r"شغل|نفذ|أنشئ ملف|انشئ ملف|اقرأ ملف|احذف ملف|run|execute|create file|read file|delete file|```"
    timeout = 20.0

    def __init__(self):
        super().__init__()
        self.python, self.files, self.system = PythonExecutorTool(), FileManagerTool(), SystemTaskTool()
        self.critic = CriticSecurityAgent()

    def handle(self, task: Task) -> AgentResult:
        if task.intent != "file" and (not task.allow_exec or SAFE_MODE):
            self.step("سَداة رفضت التنفيذ", "الطلب ليس من جهاز المطوّر أو الوضع الآمن مفعّل", "warn")
            return self.fail(LOCAL_ONLY[task.lang])
        if task.intent == "file":
            plan = planner.plan_file(task.text)
            self.step(f"سَداة تدير الملفات: {plan['action']}", str(plan["args"])[:200])
            if plan["action"] in ("create", "read", "delete") and not plan["args"].get("name"):
                return self.fail("لم أجد اسم الملف، مثلاً: notes.txt")
            res = getattr(self.files, plan["action"])(**plan["args"])
        elif task.intent == "system":
            command = planner.plan_system(task.text)["args"].get("command", "")
            issues = self.critic.check_command(command)
            self.step("الناقد يفحص الأمر", "؛ ".join(issues) or command, "warn" if issues else "ok")
            if not command or issues:
                return self.fail("؛ ".join(issues) or "لم أجد أمرًا؛ ضعه بين علامتي ` مثل `dir`")
            res = self.system.run(command)
        else:
            plan = planner.plan_python(task.text)
            code = plan["args"].get("code", "")
            issues = [i for i in scan_code(code) if i.startswith(("خطأ",) + HARD_BLOCK)]
            self.step("الناقد يفحص الكود (AST) قبل تشغيله", "؛ ".join(issues) or "لا مشكلات", "warn" if issues else "ok")
            if issues:
                return self.fail("⛔ " + "؛ ".join(issues))
            res = self.python.run(code)
        if not res.ok:
            return self.fail(res.output)
        output = f"**{res.output}**" if "\n" not in res.output and len(res.output) < 160 else f"```\n{res.output}\n```"
        self.step("نُفّذ داخل مجلد workspace", confidence=0.9)
        return self.ok(output, 0.9, data={"files": res.files})
