// Site search. Loaded only on /search/ — every other page ships nav.js alone.
//
// The index is title + URL + a short summary + one keyword, about 2 KB
// gzipped. No body text, and no search library: lunr is 29 KB gzipped and
// Fuse adds fuzzy matching nobody asked for. All-terms-must-match over 25
// entries is both faster and more predictable than either.

const input = document.getElementById("q");
const results = document.getElementById("search-results");
const status = document.getElementById("search-status");
const fallback = document.getElementById("search-fallback");

let index = null;

const esc = (s) =>
  s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Wrap each matched term so people can see why a result came back.
function mark(text, terms) {
  let out = esc(text);
  for (const t of terms) {
    out = out.replace(
      new RegExp(`(${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"),
      "<mark>$1</mark>");
  }
  return out;
}

function score(entry, terms) {
  const title = entry.t.toLowerCase();
  const summary = (entry.s || "").toLowerCase();
  const key = (entry.k || "").toLowerCase();
  let total = 0;
  for (const t of terms) {
    // Every term has to appear somewhere, or this is not a match at all.
    if (!title.includes(t) && !summary.includes(t) && !key.includes(t)) return 0;
    if (title.includes(t)) total += 3;
    if (key.includes(t)) total += 2;
    if (summary.includes(t)) total += 1;
    if (title.startsWith(t)) total += 2;
  }
  return total;
}

function render(query) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) {
    results.hidden = true;
    status.hidden = true;
    fallback.hidden = false;
    return;
  }

  const hits = index
    .map((e) => ({ e, s: score(e, terms) }))
    .filter((h) => h.s > 0)
    .sort((a, b) => b.s - a.s)
    .slice(0, 12);

  fallback.hidden = hits.length > 0;
  status.hidden = false;
  status.textContent = hits.length
    ? `${hits.length} result${hits.length === 1 ? "" : "s"} for “${query}”`
    : `Nothing found for “${query}”. Try a shorter word, or browse below.`;

  results.hidden = hits.length === 0;
  results.innerHTML = hits
    .map(({ e }) => {
      const pdf = e.u.endsWith(".pdf");
      return `<li class="search-result">
        <a href="${esc(e.u)}">
          <span class="search-result__title">${mark(e.t, terms)}${
            pdf ? ' <span class="badge">PDF</span>' : ""}</span>
          ${e.s ? `<span class="search-result__summary">${mark(e.s, terms)}</span>` : ""}
        </a>
      </li>`;
    })
    .join("");
}

async function load() {
  if (index) return;
  const res = await fetch("/index.json");
  index = await res.json();
}

async function run(query) {
  try {
    await load();
    render(query);
  } catch {
    // Leave the browse-by-section fallback in place rather than showing an
    // error nobody can act on.
    status.hidden = false;
    status.textContent = "Search is unavailable right now. Try the sections below.";
  }
}

// Answer the ?q= the form submitted, then search as the visitor types.
const initial = new URLSearchParams(location.search).get("q") || "";
if (initial) {
  input.value = initial;
  run(initial);
}

let timer;
input.addEventListener("input", () => {
  clearTimeout(timer);
  const q = input.value.trim();
  timer = setTimeout(() => {
    run(q);
    // Keep the URL shareable without adding a history entry per keystroke.
    const url = q ? `?q=${encodeURIComponent(q)}` : location.pathname;
    history.replaceState(null, "", url);
  }, 120);
});
