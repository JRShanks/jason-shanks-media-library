/* ============================================================
   Jason Shanks Media Library — Frontend Application
   Vanilla JS: loads JSON, renders cards, handles search/filter
   ============================================================ */

(function () {
  "use strict";

  // --- State ---
  let allItems = [];
  let activeCategory = "All";
  let searchQuery = "";

  // --- DOM refs ---
  const grid = document.getElementById("media-grid");
  const searchBox = document.getElementById("search-box");
  const filterContainer = document.getElementById("filter-buttons");
  const statsEl = document.getElementById("stats");

  // --- Load data ---
  async function loadData() {
    try {
      const resp = await fetch("data/media_links.json");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      allItems = await resp.json();
      // Only show verified items on the public page
      allItems = allItems.filter((item) => item.verified !== false);
      // Sort newest first
      allItems.sort((a, b) => (b.date || "").localeCompare(a.date || ""));
      render();
    } catch (err) {
      grid.innerHTML = `
        <div class="empty-state">
          <p>Unable to load media library data.</p>
          <p style="font-size:0.8rem; margin-top:0.5rem;">${err.message}</p>
        </div>`;
    }
  }

  // --- Filtering ---
  function getFiltered() {
    return allItems.filter((item) => {
      // Category filter
      if (activeCategory !== "All" && item.category !== activeCategory) {
        return false;
      }
      // Search filter
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const haystack = [
          item.title,
          item.description,
          item.source,
          ...(item.tags || []),
        ]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }

  // --- Rendering ---
  function formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      const d = new Date(dateStr + "T00:00:00");
      return d.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateStr;
    }
  }

  function renderCard(item) {
    const tagsHtml = (item.tags || [])
      .filter((t) => t && !["web-search", "YouTube", "RSS"].includes(t))
      .slice(0, 4)
      .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
      .join("");

    return `
      <a href="${escapeAttr(item.url)}" target="_blank" rel="noopener noreferrer" class="media-card">
        <div class="card-top">
          <span class="category-badge ${escapeAttr(item.category)}">${escapeHtml(item.category)}</span>
          <span class="card-source">${escapeHtml(item.source)}</span>
        </div>
        <div class="card-title">${escapeHtml(item.title)}</div>
        ${item.description ? `<div class="card-description">${escapeHtml(item.description)}</div>` : ""}
        <div class="card-meta">
          ${item.date ? `<span class="card-date">${formatDate(item.date)}</span>` : ""}
          ${tagsHtml ? `<div class="card-tags">${tagsHtml}</div>` : ""}
        </div>
      </a>`;
  }

  function render() {
    const filtered = getFiltered();
    statsEl.textContent = `Showing ${filtered.length} of ${allItems.length} items`;

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <p>No results found.</p>
        </div>`;
      return;
    }

    grid.innerHTML = filtered.map(renderCard).join("");
  }

  // --- Security helpers ---
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return (str || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // --- Event handlers ---
  function setupSearch() {
    let debounce;
    searchBox.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        searchQuery = searchBox.value.trim();
        render();
      }, 200);
    });
  }

  function setupFilters() {
    const categories = ["All", "Video", "Podcast", "Article", "Talk"];
    filterContainer.innerHTML = categories
      .map(
        (cat) =>
          `<button class="filter-btn ${cat === "All" ? "active" : ""}" data-category="${cat}">${cat}</button>`
      )
      .join("");

    filterContainer.addEventListener("click", (e) => {
      const btn = e.target.closest(".filter-btn");
      if (!btn) return;
      activeCategory = btn.dataset.category;
      filterContainer
        .querySelectorAll(".filter-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      render();
    });
  }

  // --- Embed mode detection ---
  function checkEmbedMode() {
    const params = new URLSearchParams(window.location.search);
    if (params.get("embed") === "true") {
      document.body.classList.add("embed-mode");
    }
  }

  // --- Init ---
  function init() {
    checkEmbedMode();
    setupSearch();
    setupFilters();
    loadData();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
