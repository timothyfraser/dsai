# 📌 ACTIVITY

## Run a Spatial Data Fixer Agent

🕒 *Estimated Time: 10–15 minutes*

---

## 📋 Overview

You will run **[`fixer/fixer_parcels.R`](fixer/fixer_parcels.R)** and **[`fixer/fixer_pois.R`](fixer/fixer_pois.R)**, *or* the Python twins **[`fixer/fixer_parcels.py`](fixer/fixer_parcels.py)** and **[`fixer/fixer_pois.py`](fixer/fixer_pois.py)**. Each script calls a **model API** with **batched tool calls** (one **model call per chunk** of rows): parcels get **`record_parcel_zoning`** from **polygon** rows (**`wkt`** in WGS84); POIs get **`record_poi_category`** from **point** rows (**`x`**, **`y`**). Outputs are enriched CSVs, **audit JSONL** files, and **before/after** maps (**`sf`** + **`ggplot2`** in R, **`geopandas`** + **`matplotlib`** in Python) under **`fixer/output/`**.

More detail: **[`fixer/README.md`](fixer/README.md)**.

---

## ✅ Your Task

### 🧱 Stage 1: Environment

- [ ] **R track:** Install **`dplyr`**, **`readr`**, **`jsonlite`**, **`purrr`**, **`sf`**, **`ggplot2`**, **`httr2`**, **`future`**, and **`furrr`**.
- [ ] **Python track:** **`pip install -r 10_data_management/fixer/requirements.txt`**.
- [ ] Same **`fixer/.env`** as the CSV activity: **`GEMINI_API_KEY`**, **`LLM_BASE_URL`**, **`LLM_MODEL`**. Get a free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). The free tier may use your prompts to improve Google's products, so send only public or made-up data. To run it on your own computer instead, run `ollama pull granite4:3b`, then set **`LLM_BASE_URL=http://localhost:11434/v1`** and **`LLM_MODEL=granite4:3b`** (no key needed).
- [ ] Confirm **`fixer/data/parcels_zoning_raw.csv`** (polygons in **`wkt`**) and **`fixer/data/pois_messy_raw.csv`** exist.

### 🧱 Stage 2: Run and verify

- [ ] **R:** **`Rscript 10_data_management/fixer/fixer_parcels.R`** and **`Rscript 10_data_management/fixer/fixer_pois.R`** from the **`dsai`** repo root (or use **`FIXER_ROOT`** as in **[`fixer/README.md`](fixer/README.md)**).
- [ ] **Python:** **`python 10_data_management/fixer/fixer_parcels.py`** and **`python 10_data_management/fixer/fixer_pois.py`** — same **`output/`** artifacts as R.
- [ ] Open **`fixer/output/parcels_enriched.csv`** or **`fixer/output/pois_enriched.csv`** and note at least one LLM-derived column (for example **`primary_land_use`** or **`normalized_category`**). If **`error_flag`** is **`TRUE`** anywhere, note one row and what you might try next (model, **`ROWS_PER_BATCH`**, or connectivity).
- [ ] Open **`fixer/output/map_parcels_before.png`** and **`map_parcels_after.png`** (or the POI pair) and compare how the map encoding changed.

### 🧱 Stage 3 (optional) — Contextual spatial routing

- [ ] After enriched CSVs exist, run **`Rscript 10_data_management/fixer/fixer_spatial_context.R`** *or* **`python 10_data_management/fixer/fixer_spatial_context.py`**. The LLM chooses **`nearest_poi`** / **`count_pois_within`** / **`record_context_note`** from **zone_code** and **primary_land_use**; **sf** (R) or **geopandas** (Python) computes distances and counts. Inspect **`fixer/output/parcels_context_enriched.csv`** and **`fixer/output/context_routing_audit.jsonl`**.

---

# 📤 To Submit

- Screenshot of **one** enriched map (**`map_parcels_after.png`** or **`map_pois_after.png`**) from **`fixer/output/`**.
- One sentence: what does **`primary_land_use`** add that raw **`zone_code`** alone does not express?

---


## 💡 Building similar scripts (Cursor)

If you use **Cursor** with this repository, these **Agent Skills** under [`.cursor/skills/`](../.cursor/skills/) can help when you write your own batched LLM + R workflows (including GIS tool routing like **`fixer_spatial_context.R`**):

- **[`data-science-agent-loop`](../.cursor/skills/data-science-agent-loop/SKILL.md)** — short-lived agent loops: `.env`, batch size, tool design (model routes tools; code runs **sf**), and contrast with **`agentr`** / **`agentpy`**.
- **[`console-message`](../.cursor/skills/console-message/SKILL.md)** — clear console progress for long runs (paths, chunk counts, previews).
- **[`tidyverse-elegant-r`](../.cursor/skills/tidyverse-elegant-r/SKILL.md)** — course R style: **`=`**, native **`|>`**, explicit **`library()`**, **httr2**, vectorized tables.
- **Python:** same loop patterns with **pandas** / **geopandas**; see **[`fixer/README.md`](fixer/README.md)**.


---

![](../docs/images/icons.png)

---

← 🏠 [Back to Top](#ACTIVITY)
