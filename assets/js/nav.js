// Menu polish. The menu is a native <details> element, so it already opens,
// closes and works from the keyboard with no JavaScript. This only adds the
// two behaviours <details> does not give you for free.
//
// If this file fails to load, the menu still works.

const nav = document.getElementById("site-nav");

if (nav) {
  const summary = nav.querySelector("summary");

  const close = () => {
    nav.open = false;
  };

  // Escape closes the menu and returns focus to the button that opened it.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && nav.open) {
      close();
      summary?.focus();
    }
  });

  // Clicking anywhere outside closes it.
  document.addEventListener("click", (e) => {
    if (nav.open && !nav.contains(e.target)) close();
  });

  // Mirror the open state for screen readers.
  nav.addEventListener("toggle", () => {
    summary?.setAttribute("aria-expanded", String(nav.open));
  });

  summary?.setAttribute("aria-expanded", String(nav.open));
}
