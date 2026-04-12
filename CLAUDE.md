# Weight Tracker

**Owner:** Dr. Alex Leith (personal project)
**Status:** Active development
**Purpose:** Parse daily weight from life-os health log, model expected trajectory, generate dashboard visualizations across all surfaces (wallpaper, browser, Obsidian).

## Architecture

- **Source of truth:** `C:\life-os\personal\health\health-log.md` (append-only markdown)
- **Start date:** March 16, 2026 (Day 0 = 660 lbs)
- **Model:** Piecewise linear based on TDEE decline + metabolic adaptation + tirzepatide + keto
- **Outputs:** PNG wallpaper, JSON data, HTML dashboard, Obsidian dashboard note

## Key Files

| File | Purpose |
|------|---------|
| `src/parser.py` | Parse health-log.md for weight entries |
| `src/model.py` | Piecewise expected-weight model |
| `src/wallpaper.py` | Generate matplotlib dashboard PNG + set as wallpaper |
| `src/server.py` | Flask micro-server for browser new-tab |
| `src/watcher.py` | Watchdog file monitor, triggers regeneration |
| `static/dashboard.html` | Chart.js browser dashboard |
| `config.yaml` | Paths, resolutions, model parameters |
| `run.py` | CLI entry point |

## Data Flow

```
health-log.md → parser.py → model.py → wallpaper.py → PNG → Windows wallpaper
                                      → server.py → JSON → dashboard.html → browser new tab
                                      → weight-dashboard.md (Obsidian DataviewJS)
```

## Commands

```bash
python run.py wallpaper     # Generate + set wallpaper
python run.py serve         # Start localhost dashboard server
python run.py watch         # Watch health-log.md for changes, auto-regenerate
python run.py json          # Export weight data as JSON
python run.py all           # Wallpaper + serve + watch
```
