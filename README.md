# Meetup Event Data Exporter

![Data Science Club Belgrade](assets/group_cover.jpeg)

Export past events, cover photos, and attendee lists from Meetup.com groups without PRO or API access.

## Disclaimer

This software is provided for educational and research purposes only. It is not intended for production use or for making real-world decisions. The authors make no guarantees regarding accuracy, completeness, or fitness for any particular purpose.

By using this software, you agree that you are solely responsible for any outcomes resulting from its use.

## About

Built for **Data Science Club Meetup** (Belgrade, Serbia) -- a community of 822 members (4.8/5 rating) that gathers Data Science, ML, and AI professionals, entrepreneurs, students, and enthusiasts. All events are free and open.

This tool simulates the browser's GraphQL API calls to Meetup.com to download event data, cover photos, and attendee lists into a structured local folder.

## Setup

```bash
pip install -r requirements.txt
```

Place your Meetup authentication cookie in a `.cookie` file in the project root.

## Usage

### Phase 1: Download event data

```bash
python get_events_data.py data-science-club-belgrade
```

Downloads raw JSON API responses to the `json/` folder. The script paginates through all past events automatically.

### Phase 2: Process events and download assets

```bash
python process_events.py
```

Reads JSON data from `json/`, validates it, and for each event:
- Creates a dedicated folder with cover photo and attendee list
- Aggregates all event metadata into `events/events.csv`

Re-running either script is safe -- already-downloaded files are skipped.

### Phase 3: Generate and serve the web application

```bash
python prepare_web_data.py
cd web && python -m http.server 8000
```

Processes event data and group info into a static single-page web application. Open `http://localhost:8000` to view the event gallery with group information, administrator list, and individual event detail pages.

## Folder Structure

```
.cookie                          # Meetup authentication cookie
requirements.txt                 # Python dependencies
get_events_data.py               # Phase 1: download event JSON data
process_events.py                # Phase 2: process and export
prepare_web_data.py              # Phase 3: generate static web app
models.py                        # Shared Pydantic data models

json/                            # Raw API response JSON files
  events_page_1.json
  events_page_2.json
  ...

events/                          # Processed event output
  events.csv                     # All events metadata
  <date>_<id>_<slug>/            # Per-event folder
    cover_photo.<ext>            # Event cover photo
    attendees_<id>.csv           # Attendee list

assets/                          # Project assets
  events_data_schema.json        # JSON schema for API responses
  group_info.md                  # Group description
  group_cover.jpeg               # Group cover image

docs/                            # Static web application
  index.html                     # SPA shell
  css/styles.css                 # Styles
  js/app.js                      # Router and renderers
  js/site_data.js                # Generated data (run prepare_web_data.py)
  images/                        # Copied images (run prepare_web_data.py)
```

## Features

- Cookie-based authentication (no API key required)
- Cursor-based pagination through all past events
- Automatic retries (up to 3 attempts per request)
- Rate limiting (random 1-3 second delays between requests)
- Idempotent -- skips already-downloaded files
- Graceful error handling -- continues processing on per-event failures
- Progress bars (tqdm) and structured logging (loguru)

## License

This project is licensed under the [MIT License](LICENSE).