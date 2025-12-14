"""OSF API scraper for discovering preregistration IDs"""

import os
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import requests


class OSFIDScraper:
    """Scraper for discovering OSF preregistration IDs from the registrations endpoint."""

    BASE_URL = "https://api.osf.io/v2/"
    REGISTRATIONS_ENDPOINT = "registrations/"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize OSF ID scraper.

        Args:
            api_token: Optional OSF API token for authenticated requests.
                      Can also be set via OSF_API_TOKEN environment variable.
        """
        self.api_token = api_token or os.getenv("OSF_API_TOKEN")
        self.session = requests.Session()

        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})

    def discover_preregistration_ids(
        self,
        max_results: Optional[int] = None,
        filter_category: bool = True,
        max_retries: int = 5,
        retry_wait: int = 5,
    ) -> List[str]:
        """
        Discover preregistration IDs from OSF registrations endpoint.

        Args:
            max_results: Maximum number of IDs to return (None for all).
            filter_category: If True, only return registrations with category="preregistration".
            max_retries: Maximum number of retry attempts for failed requests (default: 5).
            retry_wait: Number of seconds to wait between retries (default: 5).

        Returns:
            List of OSF registration IDs.
        """
        registration_ids = []
        url = urljoin(self.BASE_URL, self.REGISTRATIONS_ENDPOINT)

        if filter_category:
            url = self._add_filter(url, "filter[category]", "preregistration")

        page = 0
        while url:
            print(f"Fetching page {page}...", end=" ")

            data = self._fetch_with_retry(url, page, max_retries, retry_wait)
            if not data:
                break

            page_ids = [
                self._extract_id(reg.get("id", ""))
                for reg in data.get("data", [])
                if reg.get("id")
            ]

            registration_ids.extend(page_ids)
            print(
                f"Found {len(page_ids)} registration(s) (total: {len(registration_ids)})"
            )

            if max_results and len(registration_ids) >= max_results:
                return registration_ids[:max_results]

            url = data.get("links", {}).get("next")
            page += 1

        return registration_ids

    def _fetch_with_retry(
        self, url: str, page: int, max_retries: int, retry_wait: int
    ) -> Optional[dict]:
        """Fetch URL with retry logic. Returns JSON data or None on failure."""
        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < max_retries:
                    print(f"\nError fetching page {page}: {e}")
                    print(
                        f"Retrying in {retry_wait} seconds... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_wait)
                else:
                    print(f"\nMax retries reached for page {page}. Stopping.")
                    return None
        return None

    def _extract_id(self, reg_id: str) -> str:
        """Extract clean OSF ID from various formats (e.g., "abc12" or "https://osf.io/abc12/")."""
        if reg_id.startswith("http"):
            return reg_id.rstrip("/").split("/")[-1]
        return reg_id

    def _add_filter(self, url: str, filter_key: str, filter_value: str) -> str:
        """Add a filter parameter to a URL."""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params[filter_key] = [filter_value]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def save_ids(self, ids: List[str], output_file: Path) -> None:
        """
        Append IDs to a text file (one per line), avoiding duplicates.

        Args:
            ids: List of OSF IDs
            output_file: Path to output file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        existing_ids = set()
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
            print(
                f"\nAppended {len(new_ids)} new IDs to {output_file} "
                f"(skipped {len(ids) - len(new_ids)} duplicates)"
            )
        else:
            print(
                f"\nNo new IDs to append (all {len(ids)} IDs already exist in {output_file})"
            )
