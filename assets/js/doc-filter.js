// Filter for the document library. Loaded only on /documents/.
//
// Hugo renders every row, grouped under category headings, so the page is
// complete before this file arrives. The controls are rendered with `hidden`
// and revealed here — which means a visitor without JavaScript sees all the
// documents and no dead buttons, rather than a filter bar that does nothing.

const bar = document.getElementById("doc-filter");
if (bar) {
  const search = document.getElementById("doc-search");
  const count = document.getElementById("doc-count");
  const docs = [...document.querySelectorAll(".doc")];
  const groups = [...document.querySelectorAll(".doc-group")];
  const chips = [...bar.querySelectorAll("[data-filter]")];

  bar.hidden = false;

  let category = new URLSearchParams(location.search).get("category") || "all";
  if (!chips.some((c) => c.dataset.filter === category)) category = "all";

  function apply() {
    const q = (search.value || "").trim().toLowerCase();
    let shown = 0;

    for (const doc of docs) {
      const okCat = category === "all" || doc.dataset.category === category;
      const okText = !q || doc.dataset.search.includes(q);
      const show = okCat && okText;
      doc.hidden = !show;
      if (show) shown++;
    }

    // Hide a category heading once everything under it is filtered out.
    for (const group of groups) {
      const any = [...group.querySelectorAll(".doc")].some((d) => !d.hidden);
      group.hidden = !any;
    }

    count.textContent =
      shown === docs.length
        ? `${docs.length} document${docs.length === 1 ? "" : "s"}`
        : `${shown} of ${docs.length} document${docs.length === 1 ? "" : "s"}`;

    for (const chip of chips) {
      chip.setAttribute("aria-pressed", String(chip.dataset.filter === category));
    }

    // Keep a filtered view linkable — "see all ACC forms" can point at
    // /documents/?category=acc and land correctly.
    const url = category === "all" ? location.pathname : `?category=${category}`;
    history.replaceState(null, "", url);
  }

  for (const chip of chips) {
    chip.addEventListener("click", () => {
      category = chip.dataset.filter;
      apply();
    });
  }

  let timer;
  search.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(apply, 100);
  });

  apply();
}
