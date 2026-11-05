// "NAWL is waking up…": the free server sleeps after 15 idle minutes and needs about a minute to start.
(function wake() {
  const screen = document.getElementById("wake");
  let shown = false;
  const timer = setTimeout(() => { shown = true; screen.classList.add("on"); }, 1500);  // only if it is slow
  const ping = () => fetch("/api/health", { cache: "no-store" }).then((r) => {
    if (!r.ok) throw new Error(r.status);
    clearTimeout(timer);
    if (shown) { screen.classList.remove("on"); loadHome(); }
  }).catch(() => setTimeout(ping, 3000));
  ping();
})();
