# Quick Setup Guide: Shared Notion Review Workspace

> **Goal**: Give Ryan a visual, Notion-native review board in under 60 seconds using Notion's free tier.

---

## 3-Step Setup

### Step 1: Create a Free Notion Page
1. In Notion, click **"+ Add a page"** (or use an existing workspace).
2. Title it: **"AI Collaborative Review — Architecture & Behavior"**.
3. Choose an icon (e.g., 🧠 or ⚡) and banner.

### Step 2: Import the Pre-Configured Kanban CSV
1. In the top-right corner of the Notion page, click the `...` menu.
2. Select **"Import"** -> **"CSV"**.
3. Upload `notion-templates/Review-Kanban-Board.csv`.
4. Notion will instantly turn it into a structured database with pre-populated tasks, priority tags, and review lenses.

### Step 3: Switch to "Board View" (Kanban)
1. At the top of the newly imported database, click **"+ Add view"**.
2. Select **"Board"**.
3. Group by: **"Status"** (`To Review` -> `In Discussion` -> `Actionable Idea` -> `Adopted`).
4. Set card preview to **"None"** and toggle on properties: `Category`, `Priority`, `Ryan's Review Lens`.

---

## Collaboration Flow
- **Ryan**: Drags cards across columns, adds comments, tags questions, or suggests UI tweaks.
- **You**: Check off reviewed items, push new sanitized updates, and align next implementation milestones.
