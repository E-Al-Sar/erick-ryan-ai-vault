# Erick × Ryan AI Knowledge Graph & Collaboration Vault

A sanitized, plain-language **`[[wikilink]]` knowledge graph (Quartz 4 / Obsidian style)** built from **Erick's** canonical Johnny.Decimal + Zettelkasten vault (`00–50`) and bridged directly with **Ryan McCarthy's** (*Transmutations* / *Embroaden: Intelligence Fit to Form*) essays (`70`).

---

## 📁 Workspace Directory Structure

```text
ai-collab-portal/
├── README.md                           # Overview & quick-start guide
├── vault/                              # Sanitized, plain-English Obsidian [[wikilink]] vault (34 notes, 272 links)
│   ├── 00-Glossary-and-Index/          # 00.00 Home MOC, 00.01 Disambiguation Matrix, 00.02 Architecture Map
│   ├── 10-Harnesses-and-Agents/        # 10.01–10.05 Antigravity, Codex/Spark, Hermes, OpenCode/Maestri
│   ├── 20-Models-and-Weights/          # 20.01–20.03 Base Models, LoRA v2/v3 Adapters, oMLX & Ollama Servers
│   ├── 30-Infrastructure-and-Hosts/    # 30.01–30.06 Workstation & GPU Server Topology, Storage, Docker
│   ├── 40-Capabilities-and-Policy/     # 40.01–40.07 WORKSTYLE.md, Sync Targets, Skills, Keychain Vault, ANE
│   ├── 50-Audits-and-Benchmarks/       # 50.01–50.07 H01–H06/T01–T15 Eval Suite & Oct 2026 Postmortems
│   └── 70-Embroaden-and-Behavior-Bridge/ # 70.01–70.03 Erick × Ryan Synthesis ("Intelligence Fit to Form")
├── portal/
│   └── index.html                      # Compiled interactive Quartz-style [[wikilink]] graph & reader
├── scripts/
│   ├── build_wikilink_graph.py         # Compiles vault/**/*.md into portal/index.html (graph + backlinks)
│   ├── sanitize.py                     # Zero-dependency secret scanner & PII/topology redactor
│   └── publish_clean_mirror.py         # Squash git publisher (guarantees zero git history leaks)
├── notion-templates/
│   ├── Review-Kanban-Board.csv         # 1-click importable Notion Kanban database
│   └── Notion-Setup-Guide.md           # Setup instructions for Notion / Obsidian
└── docs/
    └── cloudflare-deployment.md        # 100% free hosting guide with Zero-Trust OTP email gate
```

---

## ⚡ Quick Start: 3 Ways to Explore & Share

### 1. Open the Interactive `[[Wikilink]]` Knowledge Graph Web App
Open `portal/index.html` in any browser for the full Quartz-style experience (2D interactive force-directed graph, bidirectional `[[wikilinks]]`, automatic "Linked Mentions" backlinks, hover preview cards, and instant search):
```bash
open portal/index.html
```

To rebuild `portal/index.html` after editing any Markdown note in `vault/`:
```bash
python3 scripts/build_wikilink_graph.py
```

### 2. Open Directly in Obsidian (or Import to Notion)
Because `vault/` is pure Markdown with standard YAML frontmatter and `[[wikilinks]]`:
- **Obsidian**: Open Obsidian → **Open folder as vault** → select `ai-collab-portal/vault`.
- **Notion**: In Notion → **Import → Markdown & CSV** → select `vault/` (plus `notion-templates/Review-Kanban-Board.csv`).

### 3. Run the Security Audit & Publish a Clean Git Mirror
Verify zero secrets, private paths, or private IPs exist anywhere in the workspace:
```bash
python3 scripts/sanitize.py --source . --check
```

Export a squashed, zero-history Git mirror for GitHub or Cloudflare Pages:
```bash
python3 scripts/publish_clean_mirror.py \
  --source . \
  --mirror-repo ../ai-collab-clean-mirror \
  --remote-url collaborator@example.com:your-user/ai-collab-public.git
```
