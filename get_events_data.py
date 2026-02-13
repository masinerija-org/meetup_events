import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger
from tqdm import tqdm

EVENTS_API_URL = "https://www.meetup.com/gql2"
SHA256_HASH = "9463f7c9ab5b08db3f2172223c806fb48993508781cd939184d9151c75214e3a"
JSON_DIR = Path("json")
COOKIE_FILE = Path(".cookie")
MAX_RETRIES = 3


def read_cookie() -> str:
    return COOKIE_FILE.read_text().strip()


def build_payload(urlname: str, before_datetime: str, cursor: str | None = None) -> dict:
    variables: dict = {
        "urlname": urlname,
        "beforeDateTime": before_datetime,
    }
    if cursor is not None:
        variables["after"] = cursor

    return {
        "operationName": "getPastGroupEvents",
        "variables": variables,
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": SHA256_HASH,
            }
        },
    }


def make_request(client: httpx.Client, payload: dict) -> httpx.Response:
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(
            "POST {} | operation={} | attempt {}/{}",
            EVENTS_API_URL,
            payload.get("operationName"),
            attempt,
            MAX_RETRIES,
        )
        try:
            response = client.post(EVENTS_API_URL, json=payload)
        except httpx.HTTPError as exc:
            logger.error("Request failed: {}", exc)
            if attempt < MAX_RETRIES:
                sleep_time = random.uniform(1, 3)
                logger.info("Sleeping {:.1f}s before retry...", sleep_time)
                time.sleep(sleep_time)
                continue
            raise

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

    raise RuntimeError(
        f"All {MAX_RETRIES} attempts failed for {payload.get('operationName')}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download past events data from Meetup GraphQL API"
    )
    parser.add_argument(
        "urlname",
        help="Meetup group URL slug (e.g. data-science-club-belgrade)",
    )
    args = parser.parse_args()

    cookie = read_cookie()
    JSON_DIR.mkdir(exist_ok=True)

    before_datetime = (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
    logger.info("Starting download for group '{}' (before={})", args.urlname, before_datetime)

    cursor: str | None = None
    has_next_page = True
    page = 0

    with httpx.Client(
        headers={"Cookie": cookie, "Content-Type": "application/json"},
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        pbar = tqdm(desc="Downloading event pages", unit="page")

        while has_next_page:
            page += 1
            payload = build_payload(args.urlname, before_datetime, cursor)
            response = make_request(client, payload)

            data = response.json()
            output_file = JSON_DIR / f"events_page_{page}.json"
            output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info("Saved {}", output_file)

            page_info = data["data"]["groupByUrlname"]["events"]["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

            pbar.update(1)

            if has_next_page:
                sleep_time = random.uniform(1, 3)
                logger.info("Sleeping {:.1f}s before next page...", sleep_time)
                time.sleep(sleep_time)

        pbar.close()

    logger.info("Done. Downloaded {} page(s) to {}/", page, JSON_DIR)


if __name__ == "__main__":
    main()