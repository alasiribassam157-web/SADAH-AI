// Thinking & consensus trace under every answer: who answered, who checked, whether they agreed, how sure, how fast.
const AGENT = /^([A-Za-z]+): /, MATH = new Set(["SymbolicMath", "NumericMath"]);
const clip = (s, n = 90) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

function buildTrace(data) {
  const steps = data.steps || [];
  const routed = steps.filter((s) => s.title.startsWith("Supervisor → ")).map((s) => s.title.slice(13));
  const final = steps.find((s) => s.stage === "result" && /ثقة\s*(\d+)%/.test(s.detail));
  const primary = final ? final.detail.split(" · ")[0] : routed[0] || "";
  const conf = final ? +final.detail.match(/ثقة\s*(\d+)%/)[1] : Math.round((data.confidence || 0) * 100);
  const check = steps.find((s) => s.title.startsWith("مقارنة المصادر: "));
  let verdict = check ? check.title.split(": ")[1] : "";
  if (!verdict) {  // no second source: an agent that checked its own result a second way (substitution, round trip, official peg)
    const own = steps.map((s) => s.title.match(/^(\w+): (تحققتُ(?!\s*من النتيجة)[^·(]*)/)).find(Boolean);
    verdict = own ? (MATH.has(own[1]) ? "math" : "own") : "";
  }
  return { primary, witnesses: routed.filter((a) => a !== primary), verdict, conf, ms: data.ms || 0,
           steps: steps.slice(0, 24).map((s) => [(s.title.match(AGENT) || [, s.stage])[1], clip(s.title.replace(AGENT, "").replace(/\s*\(\d+ ms\)$/, "")), s.status]) };
}

function traceHtml(tr) {
  if (!tr || !tr.primary) return "";
  const x = t("tr"), kind = { verified: "ok", math: "ok", own: "ok", single: "mid", conflict: "bad" }[tr.verdict];
  const badge = kind ? `<span class="tr-badge ${kind}">${x[tr.verdict]}</span>` : "";
  const who = [tr.primary, ...tr.witnesses].map((a) => `<code>${esc(a)}</code>`).join(" + ");
  return `<details class="trace"><summary><span class="tr-lbl">${x.title}</span>${who}${badge}<span class="tr-num">${tr.conf}% · ${tr.ms} ms</span></summary>
    <div class="tr-body"><dl><dt>${x.primary}</dt><dd><code>${esc(tr.primary)}</code></dd>
    <dt>${x.witness}</dt><dd>${tr.witnesses.length ? tr.witnesses.map((a) => `<code>${esc(a)}</code>`).join(" ") : x.none}</dd>
    <dt>${x.consensus}</dt><dd>${badge || x.none}</dd>
    <dt>${x.conf}</dt><dd><span class="tr-bar"><i style="width:${tr.conf}%"></i></span><code>${tr.conf}%</code></dd>
    <dt>${x.latency}</dt><dd><code>${tr.ms} ms</code></dd></dl>
    <ol class="tr-steps">${tr.steps.map(([a, s, st]) => `<li class="${st}"><code>${esc(a)}</code><span>${esc(s)}</span></li>`).join("")}</ol></div></details>`;
}
