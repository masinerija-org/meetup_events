# Meetup Data Exporter - Implementation Plan

## Context

The project needs a complete implementation of a Meetup.com event data exporter for groups without PRO/API access. The target group is Data Science Club Belgrade. Existing assets (`.cookie`, `assets/events_data_schema.json`, `assets/group_info.md`, `assets/group_cover.jpeg`) are in place. All Python scripts, models, and documentation need to be created from scratch.

## Files to Create (in order)

### 1. `requirements.txt`
Four dependencies, no version pinning: `pydantic`, `httpx`, `loguru`, `tqdm`

### 2. `models.py` - Shared Pydantic Models

**API Response models** (mirror `assets/events_data_schema.json`):
- `PageInfo` (endCursor, hasNextPage)
- `Venue` (id, name, address, city, state, country)
- `Going` (totalCount)
- `FeaturedEventPhoto` (id, baseUrl, highResUrl)
- `EventNode` (id, title, eventUrl, description, venue: Optional, dateTime, createdTime, endTime, going, featuredEventPhoto: Optional)
- `EventEdge` (node: EventNode)
- `Events` (totalCount, pageInfo, edges)
- `GroupByUrlname` (id, events)
- `EventsApiResponse` (data wrapper -> groupByUrlname)

**Export model** for CSV:
- `EventRecord` with flattened fields (event_id, title, event_url, description, venue_name/address/city/country, date_time, created_time, end_time, going_count, featured_photo_url, cover_image)
- `from_event_node()` classmethod to map from `EventNode` to `EventRecord`

**Attendees response model**:
- `AttendeeReportResponse` (data -> generateEventAttendeesReport -> url)

### 3. `get_events_data.py` - Phase 1 Script

- Accept `urlname` as CLI argument via `argparse`
- Read cookie from `.cookie`
- POST to `https://www.meetup.com/gql2` with `getPastGroupEvents` GraphQL payload
- `beforeDateTime` = current UTC time in ISO format (generated once at start)
- Paginate via `pageInfo.hasNextPage` / `pageInfo.endCursor`
- Save each response as `json/events_page_1.json`, `events_page_2.json`, etc.
- Rate limiting: random 1-3s sleep between requests
- Retry: up to 3 attempts per request with sleep between retries
- Logging: loguru, INFO for 2xx, ERROR with body for non-2xx
- Progress bar: tqdm (counter mode, total unknown)

### 4. `process_events.py` - Phase 2 Script

- Read all JSON files from `json/`, validate with Pydantic models
- For each event (tqdm progress bar, try/except for graceful error handling):
  - Create folder: `events/<YYYY-MM-DD>_<id>_<slug>/` (slug = first 40 chars of title, slugified via regex)
  - Download cover photo from `featuredEventPhoto.highResUrl` -> `cover_photo.<ext>` (detect extension from URL or Content-Type, default `.jpeg`)
  - Download attendees CSV: POST `generateEventAttendeesReport` -> get URL -> GET CSV -> save as `attendees_<id>.csv`
  - Skip downloads if files already exist (idempotent)
- Write `events/events.csv` from all `EventRecord` objects using `csv.DictWriter`
- Same HTTP conventions: cookie auth, rate limiting, retries, logging

### 5. Documentation

- **PLAN.md** - Save this approved plan
- **DELIVERY_REPORT.md** - Compare implementation against SPECS_1.md, report on coverage
- **README.md** - GitHub landing page with group cover image, description from `group_info.md`, folder structure, usage examples, MIT license
- **CLAUDE.md** - Update with reference to `models.py`

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Slugification | Manual via `re.sub(r"[^a-z0-9]+", "-", text)` | Avoids extra dependency |
| `eventUrl` vs `eventURL` | Use `eventUrl` | Matches actual API JSON (confirmed in CLAUDE.md) |
| Null venue/photo | `Optional` fields with `None` default | Handles online events gracefully |
| Cover photo extension | Parse from URL path, fallback to Content-Type, default `.jpeg` | Robust detection |
| Date in folder name | Parse ISO datetime, format as `YYYY-MM-DD` | Clean, sortable |
| Shared HTTP code | Duplicated in each script (small helpers) | Keeps scripts self-contained per spec |
| events.csv writing | Write after all events processed | Avoids corrupt partial CSV |
| Phase 1 JSON parsing | Dict access (not Pydantic) for pagination | Only needs 2 fields; full validation in Phase 2 |

## Verification

1. `pip install -r requirements.txt` - installs without errors
2. `python get_events_data.py data-science-club-belgrade` - downloads JSON pages to `json/`
3. `python process_events.py` - processes events, creates `events/` structure with cover photos, attendees CSVs, and `events.csv`
4. Re-running either script skips already-downloaded files (idempotency)
5. Review `DELIVERY_REPORT.md` for spec compliance