# Web Application Plan

## Overview

Static one-pager web application for Data Science Club Meetup, built with vanilla HTML/CSS/JS and hash-based routing. No backend, no build tools.

## Architecture

- **`prepare_web_data.py`** (project root): Python script that reads `events/events.csv` and `assets/group_info.md`, converts markdown descriptions to HTML, copies images, and outputs `web/js/site_data.js`
- **`web/`**: Self-contained static web application

## File Structure

```
prepare_web_data.py
web/
  index.html                    # SPA shell
  css/
    styles.css                  # Layout, components, responsive design
  js/
    site_data.js                # Generated data (const SITE_DATA = {...})
    app.js                      # Router + page renderers
  images/
    group_cover.jpeg            # From assets/
    events/<event_id>.jpeg      # From events/<folder>/cover_photo.jpeg
```

## Routes

- `#/` — Landing page (hero, events gallery, administrators, footer)
- `#/event/<event_id>` — Event detail (hero, title, description, venue, date, back button)

## Implementation Steps

1. Create `prepare_web_data.py` — parse group_info.md, read events.csv, convert descriptions to HTML via `markdown` library, copy images to `web/images/`, write `web/js/site_data.js`
2. Create `web/index.html` — minimal SPA shell with `<div id="app">`
3. Create `web/css/styles.css` — CSS Grid layouts, responsive breakpoints (3→2→1 cols for events, 4→2 cols for admins)
4. Create `web/js/app.js` — hash-based router, template-literal renderers for home and event pages
5. Update `.gitignore` — exclude generated images and site_data.js
6. Update `CLAUDE.md` and `README.md` with Phase 3 documentation

## Data Flow

```
assets/group_info.md  ──┐
assets/group_cover.jpeg ─┤
events/events.csv ───────┤──→ prepare_web_data.py ──→ web/js/site_data.js
events/*/cover_photo.* ──┘                        ──→ web/images/
```

## Verification

```bash
python prepare_web_data.py
cd web && python -m http.server 8000
# Open http://localhost:8000
```