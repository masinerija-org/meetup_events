import csv
import json
import re
import shutil
from pathlib import Path

from loguru import logger
from markdown import markdown

ASSETS_DIR = Path("assets")
EVENTS_DIR = Path("events")
WEB_DIR = Path("docs")
WEB_IMAGES_DIR = WEB_DIR / "images"
WEB_EVENTS_IMAGES_DIR = WEB_IMAGES_DIR / "events"
WEB_JS_DIR = WEB_DIR / "js"


def parse_group_info(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    group_name = ""
    members = 0
    rating = ""
    ratings_number = 0
    description_lines: list[str] = []
    administrators: list[dict] = []

    section = None
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("Group name:"):
            group_name = stripped.split(":", 1)[1].strip()
            section = None
        elif stripped.startswith("Members:"):
            members = int(stripped.split(":", 1)[1].strip())
            section = None
        elif stripped.startswith("Rating:"):
            rating = stripped.split(":", 1)[1].strip()
            section = None
        elif stripped.startswith("Ratings number:"):
            ratings_number = int(stripped.split(":", 1)[1].strip())
            section = None
        elif stripped == "Group description:":
            section = "description"
        elif stripped == "Group administrators:":
            section = "administrators"
        elif section == "description" and stripped:
            description_lines.append(stripped)
        elif section == "administrators" and stripped.startswith("- "):
            name = stripped[2:].strip()
            administrators.append({"name": name})

    return {
        "name": group_name,
        "description": " ".join(description_lines),
        "members": members,
        "rating": rating,
        "ratings_number": ratings_number,
        "cover_image": "images/group_cover.jpeg",
        "administrators": administrators,
    }


def load_events(path: Path) -> list[dict]:
    events = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            description_html = markdown(
                row["description"],
                extensions=["nl2br"],
            )
            events.append(
                {
                    "event_id": row["event_id"],
                    "title": row["title"],
                    "description": description_html,
                    "venue_name": row["venue_name"] or None,
                    "venue_city": row["venue_city"] or None,
                    "date_time": row["date_time"],
                    "going_count": int(row["going_count"]),
                    "cover_image": f"images/events/{row['event_id']}.jpeg"
                    if row.get("cover_image")
                    else None,
                }
            )

    events.sort(key=lambda e: e["date_time"], reverse=True)
    logger.info("Loaded {} events from {}", len(events), path)
    return events


def copy_images(events_csv_path: Path) -> None:
    WEB_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    WEB_EVENTS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    group_cover_src = ASSETS_DIR / "group_cover.jpeg"
    group_cover_dst = WEB_IMAGES_DIR / "group_cover.jpeg"
    if group_cover_src.exists() and not group_cover_dst.exists():
        shutil.copy2(group_cover_src, group_cover_dst)
        logger.info("Copied group cover → {}", group_cover_dst)

    with open(events_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cover_path = row.get("cover_image")
            if not cover_path:
                continue
            src = Path(cover_path)
            dst = WEB_EVENTS_IMAGES_DIR / f"{row['event_id']}.jpeg"
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                logger.info("Copied event cover {} → {}", src.name, dst)


def build_site_data(group_info: dict, events: list[dict]) -> dict:
    return {"group": group_info, "events": events}


def write_site_data_js(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    js_content = f"const SITE_DATA = {json_str};\n"
    path.write_text(js_content, encoding="utf-8")
    logger.info("Wrote site data → {}", path)


def main() -> None:
    logger.info("Preparing web data...")

    WEB_DIR.mkdir(exist_ok=True)
    (WEB_DIR / "css").mkdir(exist_ok=True)
    WEB_JS_DIR.mkdir(exist_ok=True)

    group_info = parse_group_info(ASSETS_DIR / "group_info.md")
    logger.info(
        "Group: {} | {} administrators",
        group_info["name"],
        len(group_info["administrators"]),
    )

    events_csv = EVENTS_DIR / "events.csv"
    events = load_events(events_csv)

    copy_images(events_csv)

    site_data = build_site_data(group_info, events)
    write_site_data_js(site_data, WEB_JS_DIR / "site_data.js")

    logger.info("Done. Web data prepared in {}/", WEB_DIR)


if __name__ == "__main__":
    main()