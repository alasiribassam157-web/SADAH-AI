// Opening sequence: shown for 2.2 s on every page load, then the chat opens. A tap skips it; reduced-motion users never see it.
(function intro() {
  const screen = document.getElementById("intro");
  if (!screen) return;
  const close = () => { screen.classList.add("out"); setTimeout(() => screen.remove(), 450); };
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return screen.remove();
  const timer = setTimeout(close, 2200);
  screen.addEventListener("click", () => { clearTimeout(timer); close(); });
})();
