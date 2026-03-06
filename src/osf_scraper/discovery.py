"""OSF API client for discovering preregistration IDs."""

import logging
import os
import random
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

logger = logging.getLogger(__name__)


class OSFIDScraper:
    """Scraper for discovering OSF preregistration IDs from the registrations endpoint."""

    BASE_URL = "https://api.osf.io/v2/"
    REGISTRATIONS_ENDPOINT = "registrations/"

    def __init__(self, api_token: str | None = None):
        """
        Initialise the OSF ID scraper.

        Args:
            api_token: Optional OSF API token for authenticated requests.
                      Can also be set via the ``OSF_API_TOKEN`` environment variable.
        """
        self.api_token = api_token or os.getenv("OSF_API_TOKEN")
        self.session = requests.Session()

        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})

    def discover_preregistration_ids(
        self,
        max_results: int | None = None,
        filter_category: bool = True,
        max_retries: int = 5,
        retry_wait: int = 5,
    ) -> list[str]:
        """
        Discover preregistration IDs from the OSF registrations endpoint.

        Args:
            max_results: Maximum number of IDs to return (``None`` for all).
            filter_category: If ``True``, only return registrations whose
                category is ``"preregistration"``.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_wait: Base number of seconds to wait between retries.

        Returns:
            List of OSF registration IDs.
        """
        registration_ids: list[str] = []
        url = self.BASE_URL + self.REGISTRATIONS_ENDPOINT

        if filter_category:
            url = self._add_filter(url, "filter[category]", "preregistration")

        page = 0
        while url:
            logger.info("Fetching page %d…", page)

            data = self._fetch_with_retry(url, page, max_retries, retry_wait)
            if not data:
                break

            page_ids = [
                self._extract_id(reg.get("id", ""))
                for reg in data.get("data", [])
                if reg.get("id")
            ]

            registration_ids.extend(page_ids)
            logger.info(
                "Found %d registration(s) (total: %d)",
                len(page_ids),
                len(registration_ids),
            )

            if max_results and len(registration_ids) >= max_results:
                return registration_ids[:max_results]

            url = data.get("links", {}).get("next")
            page += 1

        return registration_ids

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_with_retry(
        self, url: str, page: int, max_retries: int, retry_wait: int
    ) -> dict | None:
        """Fetch *url* with retry logic and exponential back-off."""
        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url)

                if response.status_code == 429:
                    retry_after_str = response.headers.get("Retry-After", "")
                    try:
                        base_delay = (
                            float(retry_after_str)
                            if retry_after_str
                            else retry_wait * (2**attempt)
                        )
                    except ValueError:
                        base_delay = retry_wait * (2**attempt)
                    base_delay = max(base_delay, retry_wait * (2**attempt))
                    delay = base_delay + random.uniform(0, base_delay * 0.5)
                    if attempt < max_retries:
                        logger.warning(
                            "Rate limited on page %d. "
                            "Retrying in %.1fs… (attempt %d/%d)",
                            page,
                            delay,
                            attempt + 1,
                            max_retries,
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            "Max retries reached (rate limited) for page %d. "
                            "Stopping.",
                            page,
                        )
                        return None

                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                if attempt < max_retries:
                    delay = retry_wait * (2**attempt) + random.uniform(0, retry_wait)
                    logger.warning(
                        "Error fetching page %d: %s. "
                        "Retrying in %.1fs… (attempt %d/%d)",
                        page,
                        exc,
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Max retries reached for page %d. Stopping.", page
                    )
                    return None
        return None

    @staticmethod
    def _extract_id(reg_id: str) -> str:
        """Extract a clean OSF ID from a URL or plain string."""
        if reg_id.startswith("http"):
            return reg_id.rstrip("/").split("/")[-1]
        return reg_id

    @staticmethod
    def _add_filter(url: str, filter_key: str, filter_value: str) -> str:
        """Append a query-string filter parameter to *url*."""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params[filter_key] = [filter_value]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def save_ids(self, ids: list[str], output_file: Path) -> None:
        """
        Append *ids* to a text file (one per line), skipping duplicates.

        Args:
            ids: List of OSF IDs.
            output_file: Destination file path.
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        existing_ids: set[str] = set()
        if output_file.exists():
            existing_ids = {
                line.strip()
                for line in output_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }

        new_ids = [reg_id for reg_id in ids if reg_id not in existing_ids]

        if new_ids:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write("\n".join(new_ids) + "\n")
            logger.info(
                "Appended %d new IDs to %s (skipped %d duplicates)",
                len(new_ids),
                output_file,
                len(ids) - len(new_ids),
            )
        else:
            logger.info(
                "No new IDs to append (all %d IDs already exist in %s)",
                len(ids),
                output_file,
            )
