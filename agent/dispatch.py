"""Runs an approved plan with the right tool or skill."""
from agent import composer, date_math, live_skills, markets, math_engine, prayer, safe_math, translate, units
from agent.coder import CoderSkill
from agent.tools import FileManagerTool, PythonExecutorTool, SystemTaskTool, ToolResult, WebResearchTool
from agents import supervisor

EXEC_ONLY_LOCAL = "This needs code/system execution, which is available only on the developer's machine."
TOOL_NAMES = {"python": "PythonExecutorTool", "file": "FileManagerTool", "web": "WebResearchTool",
              "system": "SystemTaskTool", "code": "CoderSkill", "weather": "WeatherSkill",
              "currency": "CurrencySkill", "datetime": "DateTimeSkill", "units": "UnitsSkill",
              "prayer": "PrayerTimesSkill", "translate": "TranslateSkill", "math": "MathEngine",
              "compare": "CompareSkill"}


class Dispatcher:
    def __init__(self):
        self.python, self.files = PythonExecutorTool(), FileManagerTool()
        self.web, self.system = WebResearchTool(), SystemTaskTool()
        self.coder = CoderSkill()
        self.last_code_task: tuple[str, float] = ("", 0.0)

    def execute(self, plan: dict, allow_exec: bool) -> ToolResult:
        tool, action, args = plan["tool"], plan["action"], plan["args"]
        if tool == "python":
            if allow_exec:
                return self.python.run(args["code"])
            if plan.get("safe"):
                try:
                    return ToolResult(True, safe_math.evaluate(plan["safe"]["op"], plan["safe"]["args"]))
                except (ValueError, ArithmeticError, SyntaxError, TypeError) as exc:
                    return ToolResult(False, f"Could not calculate: {exc}")
            return ToolResult(False, EXEC_ONLY_LOCAL)
        if tool == "file":
            return getattr(self.files, action)(**args)
        if tool == "web":
            return supervisor.research(args["query"])  # agents cross-check each other (agents/)
        if tool == "system":
            return self.system.run(args["command"]) if allow_exec else ToolResult(False, EXEC_ONLY_LOCAL)
        if tool == "code":
            result, task, conf = self.coder.answer(args["query"])
            self.last_code_task = (task, conf)
            return result
        if tool == "weather":
            return live_skills.weather(args["query"])
        if tool == "currency":
            if markets.handles(args["query"]):
                return markets.quote(args["query"])
            return live_skills.currency(args["query"])
        if tool == "datetime":
            if date_math.handles(args["query"]):
                return date_math.answer(args["query"])
            return live_skills.date_time(args["query"])
        if tool == "math":
            return math_engine.solve(args["query"])
        if tool == "compare":
            return composer.compare(args["query"])
        if tool == "units":
            return units.convert(args["query"])
        if tool == "prayer":
            return prayer.prayer_times(args["query"])
        if tool == "translate":
            return translate.translate(args["query"])
        raise ValueError(f"Unknown tool {tool}")
