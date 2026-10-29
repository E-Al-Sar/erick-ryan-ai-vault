#!/usr/bin/env python3
"""
Builds a Quartz 4 / Obsidian Publish-style interactive [[wikilink]] Knowledge Graph
web application (portal/index.html) directly from the markdown notes in vault/.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = ROOT / "vault"
OUT_HTML = ROOT / "portal" / "index.html"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]")


def parse_frontmatter(raw: str):
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    fm_text = match.group(1)
    body = raw[match.end():]
    meta = {"tags": [], "aliases": []}
    current_list = None
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line.strip().startswith("- ") and current_list is not None:
            meta[current_list].append(line.strip()[2:].strip().strip('"').strip("'"))
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if not v:
                current_list = k
                meta.setdefault(k, [])
            else:
                current_list = None
                meta[k] = v
    return meta, body


def load_vault():
    notes = {}
    for md_file in sorted(VAULT_DIR.rglob("*.md")):
        rel = md_file.relative_to(VAULT_DIR)
        folder = rel.parts[0] if len(rel.parts) > 1 else "root"
        slug = md_file.stem
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        title = meta.get("title") or slug
        note_id = meta.get("id") or slug.split("-")[0]

        # Extract plain-text preview for hover popovers
        plain = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        plain = re.sub(r"^#+\s+.*$", "", plain, flags=re.MULTILINE)
        plain = re.sub(r"> \[!\w+\]", "", plain)
        plain = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), plain)
        plain = re.sub(r"[*_`>|#-]", " ", plain)
        plain = " ".join(plain.split())[:260] + "..."

        notes[slug] = {
            "slug": slug,
            "id": str(note_id),
            "title": title,
            "folder": folder,
            "domain": meta.get("domain", folder),
            "type": meta.get("type", "note"),
            "tags": meta.get("tags", []),
            "aliases": meta.get("aliases", []),
            "updated": meta.get("updated", "2026-10-28"),
            "body": body.strip(),
            "preview": plain,
            "outgoing": [],
            "backlinks": [],
        }

    # Resolve [[wikilinks]] and populate outgoing + backlinks
    for slug, note in notes.items():
        found = []
        for match in WIKILINK_RE.finditer(note["body"]):
            target = match.group(1).strip()
            # Match exact slug or prefix ID
            resolved = None
            if target in notes:
                resolved = target
            else:
                for cand_slug in notes:
                    if cand_slug.lower() == target.lower() or cand_slug.startswith(target.split("-")[0] + "-"):
                        resolved = cand_slug
                        break
            if resolved and resolved != slug and resolved not in found:
                found.append(resolved)
        note["outgoing"] = found

    for slug, note in notes.items():
        for target in note["outgoing"]:
            if slug not in notes[target]["backlinks"]:
                notes[target]["backlinks"].append(slug)

    return notes


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Erick & Ryan — [[Wikilink]] AI Knowledge Graph (Quartz Studio)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    :root {
      --bg: #faf8f5;
      --panel-bg: #f2efe9;
      --card-bg: #ffffff;
      --text: #2b2926;
      --text-muted: #6e6a63;
      --border: #e2ddd5;
      --accent: #2b6cb0;
      --accent-soft: #e6f0fa;
      --wikilink-bg: #eaf2fb;
      --wikilink-text: #1d5696;
      --wikilink-border: #bfd8f5;
      --callout-tip-bg: #eef7f2;
      --callout-tip-border: #2f855a;
      --callout-warn-bg: #fef6e8;
      --callout-warn-border: #d69e2e;
      --code-bg: #f3f1ec;
      --font-sans: 'Atkinson Hyperlegible', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    [data-theme="dark"] {
      --bg: #161618;
      --panel-bg: #1e1e21;
      --card-bg: #242428;
      --text: #eae8e3;
      --text-muted: #9a9892;
      --border: #323237;
      --accent: #63b3ed;
      --accent-soft: #1e3246;
      --wikilink-bg: #1c3147;
      --wikilink-text: #7cc4fa;
      --wikilink-border: #2d4e70;
      --callout-tip-bg: #162c22;
      --callout-tip-border: #48bb78;
      --callout-warn-bg: #302412;
      --callout-warn-border: #ecc94b;
      --code-bg: #1c1c1f;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      display: grid;
      grid-template-columns: 300px 1fr 330px;
      height: 100vh;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Left Sidebar: Vault Explorer */
    .left-sidebar {
      background: var(--panel-bg);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    .brand-bar {
      padding: 16px 18px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .brand-title {
      font-size: 15px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
    .icon-btn {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 6px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      font-family: var(--font-sans);
    }
    .icon-btn:hover { border-color: var(--accent); }

    .search-box {
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
    }
    .search-input {
      width: 100%;
      padding: 8px 11px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 13.5px;
    }
    .search-input:focus { outline: 2px solid var(--accent); border-color: transparent; }

    .tree-container {
      flex: 1;
      overflow-y: auto;
      padding: 10px 10px 24px;
    }
    .folder-group { margin-bottom: 14px; }
    .folder-header {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      padding: 6px 8px 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .folder-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }
    .note-link {
      display: flex;
      align-items: baseline;
      gap: 7px;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 13.5px;
      color: var(--text);
      cursor: pointer;
      line-height: 1.35;
      margin-bottom: 2px;
      transition: background 0.12s;
    }
    .note-link:hover { background: var(--accent-soft); }
    .note-link.active {
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
    }
    .note-id {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      flex-shrink: 0;
    }

    /* Center Column: Note Reader */
    .center-pane {
      height: 100vh;
      overflow-y: auto;
      padding: 36px 52px 90px;
    }
    .center-inner {
      max-width: 780px;
      margin: 0 auto;
    }
    .breadcrumbs {
      font-size: 12.5px;
      color: var(--text-muted);
      font-family: var(--font-mono);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tag-row {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    .tag-pill {
      background: var(--panel-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 11.5px;
      padding: 2px 8px;
      border-radius: 12px;
      font-family: var(--font-mono);
    }

    /* Markdown Styling */
    .note-content h1 { font-size: 29px; font-weight: 700; margin-bottom: 16px; line-height: 1.25; }
    .note-content h2 { font-size: 20px; font-weight: 700; margin: 30px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
    .note-content h3 { font-size: 16.5px; font-weight: 700; margin: 22px 0 8px; }
    .note-content p { font-size: 15.5px; line-height: 1.7; margin-bottom: 14px; }
    .note-content ul, .note-content ol { padding-left: 22px; margin-bottom: 16px; }
    .note-content li { font-size: 15px; line-height: 1.65; margin-bottom: 6px; }
    .note-content hr { border: none; border-top: 1px solid var(--border); margin: 26px 0; }
    .note-content code {
      font-family: var(--font-mono);
      font-size: 13px;
      background: var(--code-bg);
      padding: 2px 5px;
      border-radius: 4px;
    }
    .note-content pre {
      background: var(--code-bg);
      border: 1px solid var(--border);
      padding: 14px 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 14px 0 18px;
    }
    .note-content pre code { padding: 0; background: none; }

    /* Tables */
    .note-content table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0 24px;
      font-size: 14px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }
    .note-content th, .note-content td {
      padding: 10px 13px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      line-height: 1.5;
      vertical-align: top;
    }
    .note-content th {
      background: var(--panel-bg);
      font-weight: 700;
      font-size: 13px;
    }

    /* Callouts */
    .callout-box {
      background: var(--callout-tip-bg);
      border-left: 4px solid var(--callout-tip-border);
      padding: 14px 18px;
      border-radius: 6px;
      margin: 16px 0 22px;
      font-size: 14.5px;
      line-height: 1.6;
    }
    .callout-box.warn {
      background: var(--callout-warn-bg);
      border-left-color: var(--callout-warn-border);
    }

    /* Interactive [[Wikilinks]] */
    .wikilink {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      background: var(--wikilink-bg);
      color: var(--wikilink-text);
      border: 1px solid var(--wikilink-border);
      padding: 1px 7px;
      border-radius: 5px;
      font-weight: 600;
      font-size: 0.94em;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.12s ease;
    }
    .wikilink:hover {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }

    /* Right Sidebar: Graph + Backlinks */
    .right-sidebar {
      background: var(--panel-bg);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow-y: auto;
      padding: 16px;
      gap: 18px;
    }
    .panel-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
    }
    .panel-header {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    #graph-canvas {
      width: 100%;
      height: 250px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      cursor: grab;
      display: block;
    }
    #graph-canvas:active { cursor: grabbing; }

    .backlink-item {
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      margin-bottom: 7px;
      cursor: pointer;
      background: var(--bg);
      transition: border-color 0.12s;
    }
    .backlink-item:hover { border-color: var(--accent); }
    .backlink-title { font-size: 13px; font-weight: 700; color: var(--accent); }
    .backlink-preview { font-size: 11.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.4; }

    /* Hover Preview Popover (Quartz 4 Style) */
    #hover-popover {
      position: fixed;
      z-index: 2000;
      width: 340px;
      background: var(--card-bg);
      border: 1px solid var(--accent);
      border-radius: 10px;
      padding: 14px 16px;
      box-shadow: 0 10px 28px rgba(0,0,0,0.18);
      pointer-events: none;
      display: none;
    }
    .pop-id { font-family: var(--font-mono); font-size: 11px; color: var(--accent); font-weight: 700; }
    .pop-title { font-size: 15px; font-weight: 700; margin: 3px 0 6px; color: var(--text); }
    .pop-body { font-size: 12.5px; color: var(--text-muted); line-height: 1.5; }

    /* Fullscreen Graph Modal */
    #graph-modal {
      position: fixed;
      inset: 0;
      background: rgba(15, 15, 18, 0.85);
      z-index: 1500;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 32px;
    }
    #graph-modal.open { display: flex; }
    .modal-inner {
      width: 100%;
      height: 100%;
      background: var(--card-bg);
      border-radius: 12px;
      border: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .modal-bar {
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    #modal-canvas {
      flex: 1;
      width: 100%;
      background: var(--bg);
      cursor: grab;
    }

    .mermaid-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 18px;
      margin: 16px 0;
      overflow-x: auto;
      display: flex;
      justify-content: center;
    }
  </style>
</head>
<body data-theme="light">

  <!-- Left Sidebar: Johnny.Decimal Vault Tree -->
  <aside class="left-sidebar">
    <div class="brand-bar">
      <div class="brand-title" onclick="openNote('70.01-Intelligence-Fit-to-Form-MOC')">
        <span>🕸️</span>
        <span>Erick × Ryan Vault</span>
      </div>
      <button class="icon-btn" onclick="toggleTheme()" title="Toggle Light/Dark">🌓</button>
    </div>

    <div class="search-box">
      <input id="search-input" class="search-input" type="text" placeholder="Search 34 notes or [[wikilinks]]... ( / )" oninput="filterTree(this.value)">
    </div>

    <div id="vault-tree" class="tree-container"></div>
  </aside>

  <!-- Center Reader -->
  <main class="center-pane" id="center-pane">
    <div class="center-inner">
      <div id="breadcrumbs" class="breadcrumbs"></div>
      <div id="tag-row" class="tag-row"></div>
      <article id="note-body" class="note-content"></article>
    </div>
  </main>

  <!-- Right Sidebar: Interactive [[Wikilink]] Graph + Backlinks -->
  <aside class="right-sidebar">
    <div class="panel-card">
      <div class="panel-header">
        <span>🕸️ [[Wikilink]] Graph</span>
        <button class="icon-btn" onclick="openFullGraph()">⛶ Expand</button>
      </div>
      <canvas id="graph-canvas" width="296" height="250"></canvas>
      <div style="font-size:11.5px; color:var(--text-muted); margin-top:8px; display:flex; flex-wrap:wrap; gap:8px;">
        <span>🟣 70 Ryan×Erick Bridge</span>
        <span>🔵 00–20 Harnesses & Models</span>
        <span>🟢 30–40 Hosts & Rules</span>
        <span>🟠 50 Crash Tests</span>
      </div>
    </div>

    <div class="panel-card">
      <div class="panel-header">
        <span>↩️ Linked Mentions (Backlinks)</span>
        <span id="backlink-count">0</span>
      </div>
      <div id="backlinks-list"></div>
    </div>

    <div class="panel-card">
      <div class="panel-header">
        <span>↪️ Outgoing [[Wikilinks]]</span>
        <span id="outgoing-count">0</span>
      </div>
      <div id="outgoing-list"></div>
    </div>
  </aside>

  <!-- Floating Hover Preview Card -->
  <div id="hover-popover">
    <div id="pop-id" class="pop-id"></div>
    <div id="pop-title" class="pop-title"></div>
    <div id="pop-body" class="pop-body"></div>
  </div>

  <!-- Fullscreen Graph Modal -->
  <div id="graph-modal">
    <div class="modal-inner">
      <div class="modal-bar">
        <strong>🕸️ Full Vault [[Wikilink]] Graph — Click Any Node to Open Note</strong>
        <button class="icon-btn" onclick="closeFullGraph()">✕ Close (Esc)</button>
      </div>
      <canvas id="modal-canvas"></canvas>
    </div>
  </div>

  <script>
    const VAULT = __VAULT_JSON__;

    const FOLDER_ORDER = [
      ["70-Embroaden-and-Behavior-Bridge", "70 · Ryan × Erick Bridge", "#805ad5"],
      ["00-Glossary-and-Index", "00 · Dictionary & Map", "#2b6cb0"],
      ["10-Harnesses-and-Agents", "10 · AI Apps (Harnesses)", "#3182ce"],
      ["20-Models-and-Weights", "20 · Brains & LoRA Packs", "#0bc5ea"],
      ["30-Infrastructure-and-Hosts", "30 · Machines & Storage", "#38a169"],
      ["40-Capabilities-and-Policy", "40 · Rules, Skills & Memory", "#2f855a"],
      ["50-Audits-and-Benchmarks", "50 · Crash Tests & Audits", "#dd6b20"]
    ];

    const FOLDER_COLORS = Object.fromEntries(FOLDER_ORDER.map(([k, _, c]) => [k, c]));
    let currentSlug = "70.01-Intelligence-Fit-to-Form-MOC";

    mermaid.initialize({ startOnLoad: false, theme: 'default' });

    function resolveSlug(target) {
      if (VAULT[target]) return target;
      const clean = target.trim().toLowerCase();
      for (const slug of Object.keys(VAULT)) {
        if (slug.toLowerCase() === clean) return slug;
        if (slug.toLowerCase().startsWith(clean.split("-")[0] + "-")) return slug;
      }
      return null;
    }

    function renderTree(filterText = "") {
      const container = document.getElementById("vault-tree");
      const q = filterText.trim().toLowerCase();
      let html = "";

      for (const [folderKey, folderLabel, color] of FOLDER_ORDER) {
        const notes = Object.values(VAULT).filter(n => n.folder === folderKey && (
          !q ||
          n.title.toLowerCase().includes(q) ||
          n.slug.toLowerCase().includes(q) ||
          n.body.toLowerCase().includes(q) ||
          n.tags.some(t => t.toLowerCase().includes(q))
        ));
        if (!notes.length) continue;

        html += `<div class="folder-group">
          <div class="folder-header"><span class="folder-dot" style="background:${color}"></span>${folderLabel}</div>`;
        for (const n of notes) {
          const active = n.slug === currentSlug ? "active" : "";
          html += `<div class="note-link ${active}" onclick="openNote('${n.slug}')">
            <span class="note-id">${n.id}</span>
            <span>${n.title.replace(/^.*?—\s*/, '')}</span>
          </div>`;
        }
        html += `</div>`;
      }
      container.innerHTML = html;
    }

    function filterTree(val) {
      renderTree(val);
    }

    function transformMarkdownWithWikilinks(md) {
      // Convert > [!TIP] / > [!WARNING] / > [!IMPORTANT] / > [!NOTE] callouts
      md = md.replace(/^> \[!(TIP|NOTE|IMPORTANT|WARNING)\]\s*\n((?:>.*(?:\n|$))+)/gm, (_, kind, content) => {
        const inner = content.replace(/^>\s?/gm, "");
        const cls = (kind === "WARNING" || kind === "IMPORTANT") ? "callout-box warn" : "callout-box";
        return `<div class="${cls}">${marked.parse(replaceWikilinksInline(inner))}</div>\n`;
      });
      return marked.parse(replaceWikilinksInline(md));
    }

    function replaceWikilinksInline(text) {
      // Protect fenced code blocks and inline backticks so `[[wikilinks]]` inside code stays literal
      const codeSlots = [];
      const protectedText = text.replace(/(`{1,3}[\s\S]*?`{1,3})/g, (m) => {
        codeSlots.push(m);
        return `@@CODE_SLOT_${codeSlots.length - 1}@@`;
      });
      const linked = protectedText.replace(/\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]/g, (_, target, alias) => {
        const slug = resolveSlug(target);
        const label = alias || target;
        if (!slug) return `<code>[[${label}]]</code>`;
        return `<a class="wikilink" href="#${slug}" data-slug="${slug}" onclick="event.preventDefault(); openNote('${slug}')" onmouseenter="showPopover(event, '${slug}')" onmouseleave="hidePopover()">🔗 ${label}</a>`;
      });
      return linked.replace(/@@CODE_SLOT_(\d+)@@/g, (_, idx) => codeSlots[Number(idx)]);
    }

    async function openNote(slug) {
      if (!VAULT[slug]) return;
      currentSlug = slug;
      window.location.hash = slug;
      hidePopover();

      const note = VAULT[slug];
      document.getElementById("breadcrumbs").innerHTML = `<span>${note.folder}</span> <span>/</span> <strong>[[${note.slug}]]</strong>`;
      document.getElementById("tag-row").innerHTML = note.tags.map(t => `<span class="tag-pill">#${t}</span>`).join("");

      const bodyEl = document.getElementById("note-body");
      bodyEl.innerHTML = transformMarkdownWithWikilinks(note.body);

      // Render Mermaid blocks
      const codeBlocks = bodyEl.querySelectorAll("pre code.language-mermaid");
      for (let i = 0; i < codeBlocks.length; i++) {
        const codeEl = codeBlocks[i];
        const graphDef = codeEl.textContent;
        const pre = codeEl.parentElement;
        const wrapper = document.createElement("div");
        wrapper.className = "mermaid-box";
        try {
          const { svg } = await mermaid.render("mermaid-" + Date.now() + "-" + i, graphDef);
          wrapper.innerHTML = svg;
          pre.replaceWith(wrapper);
        } catch (e) {}
      }

      // Render Backlinks
      const backlinks = note.backlinks.map(s => VAULT[s]).filter(Boolean);
      document.getElementById("backlink-count").textContent = backlinks.length;
      document.getElementById("backlinks-list").innerHTML = backlinks.length
        ? backlinks.map(b => `<div class="backlink-item" onclick="openNote('${b.slug}')" onmouseenter="showPopover(event, '${b.slug}')" onmouseleave="hidePopover()">
            <div class="backlink-title">[[${b.id}]] ${b.title}</div>
            <div class="backlink-preview">${b.preview.slice(0, 110)}...</div>
          </div>`).join("")
        : `<div style="font-size:12.5px; color:var(--text-muted);">No incoming links yet.</div>`;

      // Render Outgoing
      const outgoing = note.outgoing.map(s => VAULT[s]).filter(Boolean);
      document.getElementById("outgoing-count").textContent = outgoing.length;
      document.getElementById("outgoing-list").innerHTML = outgoing.length
        ? outgoing.map(o => `<div class="backlink-item" onclick="openNote('${o.slug}')" onmouseenter="showPopover(event, '${o.slug}')" onmouseleave="hidePopover()">
            <div class="backlink-title">[[${o.id}]] ${o.title}</div>
          </div>`).join("")
        : `<div style="font-size:12.5px; color:var(--text-muted);">No outgoing links.</div>`;

      document.getElementById("center-pane").scrollTop = 0;
      renderTree(document.getElementById("search-input").value);
      drawGraph(document.getElementById("graph-canvas"), false);
    }

    function showPopover(e, slug) {
      const n = VAULT[slug];
      if (!n) return;
      const pop = document.getElementById("hover-popover");
      document.getElementById("pop-id").textContent = `[[${n.slug}]]`;
      document.getElementById("pop-title").textContent = n.title;
      document.getElementById("pop-body").textContent = n.preview;
      pop.style.display = "block";
      const x = Math.min(window.innerWidth - 360, e.clientX + 14);
      const y = Math.min(window.innerHeight - 160, e.clientY + 14);
      pop.style.left = x + "px";
      pop.style.top = y + "px";
    }

    function hidePopover() {
      document.getElementById("hover-popover").style.display = "none";
    }

    // Force-Directed Knowledge Graph Engine
    function setupForceGraph(canvas, isFull) {
      const ctx = canvas.getContext("2d");
      const rect = canvas.getBoundingClientRect();
      const W = canvas.width = rect.width || (isFull ? 960 : 296);
      const H = canvas.height = rect.height || (isFull ? 640 : 250);

      const slugs = Object.keys(VAULT);
      const nodes = slugs.map((slug, idx) => {
        const angle = (2 * Math.PI * idx) / slugs.length;
        const r = Math.min(W, H) * 0.34;
        return {
          slug,
          id: VAULT[slug].id,
          title: VAULT[slug].title,
          folder: VAULT[slug].folder,
          x: W / 2 + r * Math.cos(angle),
          y: H / 2 + r * Math.sin(angle),
          vx: 0,
          vy: 0
        };
      });
      const nodeMap = Object.fromEntries(nodes.map(n => [n.slug, n]));
      const edges = [];
      for (const n of Object.values(VAULT)) {
        for (const t of n.outgoing) {
          if (nodeMap[n.slug] && nodeMap[t]) {
            edges.push([nodeMap[n.slug], nodeMap[t]]);
          }
        }
      }

      // Run 200 ticks of spring layout
      for (let step = 0; step < 200; step++) {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i], b = nodes[j];
            let dx = b.x - a.x, dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const rep = (isFull ? 11000 : 520) / (dist * dist);
            a.vx -= (dx / dist) * rep;
            a.vy -= (dy / dist) * rep;
            b.vx += (dx / dist) * rep;
            b.vy += (dy / dist) * rep;
          }
        }
        for (const [a, b] of edges) {
          let dx = b.x - a.x, dy = b.y - a.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const targetDist = isFull ? 220 : 58;
          const k = (dist - targetDist) * (isFull ? 0.018 : 0.035);
          a.vx += (dx / dist) * k;
          a.vy += (dy / dist) * k;
          b.vx -= (dx / dist) * k;
          b.vy -= (dy / dist) * k;
        }
        for (const n of nodes) {
          const grav = isFull ? 0.005 : 0.02;
          n.vx += (W / 2 - n.x) * grav;
          n.vy += (H / 2 - n.y) * grav;
          n.x = Math.max(45, Math.min(W - 165, n.x + n.vx * 0.5));
          n.y = Math.max(28, Math.min(H - 28, n.y + n.vy * 0.5));
          n.vx *= 0.6;
          n.vy *= 0.6;
        }
      }

      // Pin active node near center in mini graph
      if (!isFull && nodeMap[currentSlug]) {
        nodeMap[currentSlug].x = W / 2;
        nodeMap[currentSlug].y = H / 2;
      }

      const activeNote = VAULT[currentSlug];
      const connected = new Set([currentSlug, ...(activeNote?.outgoing || []), ...(activeNote?.backlinks || [])]);

      function render() {
        ctx.clearRect(0, 0, W, H);
        for (const [a, b] of edges) {
          const isHigh = a.slug === currentSlug || b.slug === currentSlug;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = isHigh ? "#2b6cb0" : "rgba(140,140,140,0.22)";
          ctx.lineWidth = isHigh ? 1.8 : 0.9;
          ctx.stroke();
        }
        for (const n of nodes) {
          const isCurrent = n.slug === currentSlug;
          const isNeighbor = connected.has(n.slug);
          ctx.beginPath();
          ctx.arc(n.x, n.y, isCurrent ? (isFull ? 10 : 7) : (isFull ? 6.5 : 4.5), 0, Math.PI * 2);
          ctx.fillStyle = FOLDER_COLORS[n.folder] || "#2b6cb0";
          ctx.globalAlpha = isNeighbor || isFull ? 1.0 : 0.32;
          ctx.fill();
          if (isCurrent) {
            ctx.lineWidth = 2.5;
            ctx.strokeStyle = "#ffffff";
            ctx.stroke();
          }
          if (isFull || isNeighbor) {
            ctx.font = (isCurrent ? "bold " : "") + (isFull ? "12px " : "10px ") + "Inter, sans-serif";
            ctx.fillStyle = document.body.getAttribute("data-theme") === "dark" ? "#eae8e3" : "#2b2926";
            ctx.fillText(isFull ? `${n.id} ${n.title.slice(0, 26)}` : n.id, n.x + 8, n.y + 3);
          }
        }
        ctx.globalAlpha = 1.0;
      }

      render();

      canvas.onclick = (ev) => {
        const br = canvas.getBoundingClientRect();
        const mx = ev.clientX - br.left, my = ev.clientY - br.top;
        for (const n of nodes) {
          if (Math.hypot(n.x - mx, n.y - my) < 12) {
            openNote(n.slug);
            if (isFull) closeFullGraph();
            break;
          }
        }
      };
    }

    function drawGraph(canvas, isFull) {
      setupForceGraph(canvas, isFull);
    }

    function openFullGraph() {
      const modal = document.getElementById("graph-modal");
      modal.classList.add("open");
      setTimeout(() => drawGraph(document.getElementById("modal-canvas"), true), 40);
    }

    function closeFullGraph() {
      document.getElementById("graph-modal").classList.remove("open");
    }

    function toggleTheme() {
      const next = document.body.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.body.setAttribute("data-theme", next);
      drawGraph(document.getElementById("graph-canvas"), false);
    }

    window.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement.tagName !== "INPUT") {
        e.preventDefault();
        document.getElementById("search-input").focus();
      }
      if (e.key === "Escape") closeFullGraph();
    });

    window.addEventListener("DOMContentLoaded", () => {
      const rawHash = window.location.hash.replace(/^#/, "");
      const openModal = rawHash.endsWith(":graph");
      const hash = rawHash.replace(/:graph$/, "");
      const start = resolveSlug(hash) || "70.01-Intelligence-Fit-to-Form-MOC";
      openNote(start);
      if (openModal) {
        setTimeout(() => openFullGraph(), 150);
      }
    });
  </script>
</body>
</html>
"""


def main():
    notes = load_vault()
    vault_json = json.dumps(notes, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__VAULT_JSON__", vault_json)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    root_html = ROOT / "index.html"
    root_html.write_text(html, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    total_links = sum(len(n["outgoing"]) for n in notes.values())
    print(f"[+] Built Quartz [[wikilink]] graph portal: {OUT_HTML} (and {root_html})")
    print(f"    Notes indexed: {len(notes)}")
    print(f"    Resolved [[wikilink]] edges: {total_links}")


if __name__ == "__main__":
    main()
