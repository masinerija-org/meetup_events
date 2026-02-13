import csv
import json
import os
import random
import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import httpx
from loguru import logger
from tqdm import tqdm

from models import (
    AttendeeReportResponse,
    EventNode,
    EventRecord,
    EventsApiResponse,
)

ATTENDEES_API_URL = "https://www.meetup.com/gql2"
ATTENDEES_SHA256_HASH = (
    "f7c9409796ae0724dadeaf075b883c3e6e19438387dd2c064bc075f6413a3d0e"
)
JSON_DIR = Path("json")
EVENTS_DIR = Path("events")
COOKIE_FILE = Path(".cookie")
MAX_RETRIES = 3


def read_cookie() -> str:
    return COOKIE_FILE.read_text().strip()


def slugify(text: str) -> str:
    text = text[:40]
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def get_event_folder_name(node: EventNode) -> str:
    dt = datetime.fromisoformat(node.dateTime)
    date_str = dt.strftime("%Y-%m-%d")
    slug = slugify(node.title)
    return f"{date_str}_{node.id}_{slug}"


def make_request(
    client: httpx.Client,
    url: str,
    payload: dict | None = None,
    method: str = "POST",
) -> httpx.Response | None:
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(
            "{} {} | attempt {}/{}",
            method,
            url,
            attempt,
            MAX_RETRIES,
        )
        try:
            if method == "POST":
                response = client.post(url, json=payload)
            else:
                response = client.get(url)
        except httpx.HTTPError as exc:
            logger.error("Request failed: {}", exc)
            if attempt < MAX_RETRIES:
                sleep_time = random.uniform(1, 3)
                logger.info("Sleeping {:.1f}s before retry...", sleep_time)
                time.sleep(sleep_time)
                continue
            return None

        if response.is_success:
            logger.info("Response status: {} OK", response.status_code)
            return response

        logger.error(
            "Response status: {} | body: {}",
            response.status_code,
            response.text,
        )
        if attempt < MAX_RETRIES:
            sleep_time = random.uniform(1, 3)
            logger.info("Sleeping {:.1f}s before retry...", sleep_time)
            time.sleep(sleep_time)

    logger.error("All {} attempts failed for {} {}", MAX_RETRIES, method, url)
    return None


def load_events_from_json() -> list[EventNode]:
    json_files = sorted(JSON_DIR.glob("*.json"))
    if not json_files:
        logger.warning("No JSON files found in {}/", JSON_DIR)
        return []

    all_events: list[EventNode] = []
    for json_file in json_files:
        logger.info("Reading {}", json_file)
        raw = json.loads(json_file.read_text())
        api_response = EventsApiResponse.model_validate(raw)
        for edge in api_response.data.groupByUrlname.events.edges:
            all_events.append(edge.node)

    logger.info("Loaded {} events from {} file(s)", len(all_events), len(json_files))
    return all_events


def detect_extension(url: str, response: httpx.Response) -> str:
    parsed_path = urllib.parse.urlparse(url).path
    _, ext = os.path.splitext(parsed_path)
    if ext and ext.lower() in (".jpeg", ".jpg", ".png", ".gif", ".webp"):
        return ext.lower()

    content_type = response.headers.get("content-type", "")
    ct_map = {
        "image/jpeg": ".jpeg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    for ct, extension in ct_map.items():
        if ct in content_type:
            return extension

    return ".jpeg"


def download_cover_photo(
    client: httpx.Client, node: EventNode, event_dir: Path
) -> str:
    if node.featuredEventPhoto is None:
        return ""

    existing = list(event_dir.glob("cover_photo.*"))
    if existing:
        logger.info("Cover photo already exists: {}", existing[0])
        return str(existing[0])

    url = node.featuredEventPhoto.highResUrl
    response = make_request(client, url, method="GET")
    if response is None:
        logger.error("Failed to download cover photo for event {}", node.id)
        return ""

    ext = detect_extension(url, response)
    cover_path = event_dir / f"cover_photo{ext}"
    cover_path.write_bytes(response.content)
    logger.info("Saved cover photo: {}", cover_path)
    return str(cover_path)


def download_attendees_csv(
    client: httpx.Client, event_id: str, event_dir: Path
) -> None:
    target = event_dir / f"attendees_{event_id}.csv"
    if target.exists():
        logger.info("Attendees CSV already exists: {}", target)
        return

    payload = {
        "operationName": "generateEventAttendeesReport",
        "variables": {"eventId": event_id},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": ATTENDEES_SHA256_HASH,
            }
        },
    }

    response = make_request(client, ATTENDEES_API_URL, payload=payload)
    if response is None:
        logger.error("Failed to get attendees report URL for event {}", event_id)
        return

    report = AttendeeReportResponse.model_validate(response.json())
    csv_url = report.data.generateEventAttendeesReport.url

    sleep_time = random.uniform(1, 3)
    logger.info("Sleeping {:.1f}s before downloading attendees CSV...", sleep_time)
    time.sleep(sleep_time)

    csv_response = make_request(client, csv_url, method="GET")
    if csv_response is None:
        logger.error("Failed to download attendees CSV for event {}", event_id)
        return

    target.write_bytes(csv_response.content)
    logger.info("Saved attendees CSV: {}", target)


def process_events() -> None:
    cookie = read_cookie()
    EVENTS_DIR.mkdir(exist_ok=True)

    events = load_events_from_json()
    if not events:
        logger.warning("No events to process.")
        return

    records: list[EventRecord] = []

    with httpx.Client(
        headers={"Cookie": cookie, "Content-Type": "application/json"},
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        for node in tqdm(events, desc="Processing events", unit="event"):
            try:
                folder_name = get_event_folder_name(node)
                event_dir = EVENTS_DIR / folder_name
                event_dir.mkdir(parents=True, exist_ok=True)

                cover_image = download_cover_photo(client, node, event_dir)

                sleep_time = random.uniform(1, 3)
                logger.info("Sleeping {:.1f}s before attendees request...", sleep_time)
                time.sleep(sleep_time)

                download_attendees_csv(client, node.id, event_dir)

                record = EventRecord.from_event_node(node, cover_image=cover_image)
                records.append(record)

                sleep_time = random.uniform(1, 3)
                logger.info("Sleeping {:.1f}s before next event...", sleep_time)
                time.sleep(sleep_time)

            except Exception:
                logger.exception("Error processing event {} ({})", node.id, node.title)
                continue

    csv_path = EVENTS_DIR / "events.csv"
    if records:
        fieldnames = list(EventRecord.model_fields.keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record.model_dump())
        logger.info("Saved {} event records to {}", len(records), csv_path)
    else:
        logger.warning("No records to write to CSV.")

    logger.info("Done processing {} events.", len(events))


if __name__ == "__main__":
    process_events()