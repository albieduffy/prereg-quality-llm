"""OSF API scraper for discovering preregistration IDs"""

import os
import time
import requests
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse


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
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}"
            })
    
    def discover_preregistration_ids(
        self,
        max_results: Optional[int] = None,
        filter_category: bool = True,
        max_retries: int = 5,
        retry_wait: int = 5,
        start_page: int = 0
    ) -> List[str]:
        """
        Discover preregistration IDs from OSF registrations endpoint.
        
        Args:
            max_results: Maximum number of IDs to return (None for all).
            filter_category: If True, only return registrations with category="preregistration".
            max_retries: Maximum number of retry attempts for failed requests (default: 5).
            retry_wait: Number of seconds to wait between retries (default: 5).
            start_page: Page number to start collecting IDs from (default: 0). Pages before this
                       will be skipped but still paginated through.
        
        Returns:
            List of OSF registration IDs.
        """
        registration_ids = []
        url = urljoin(self.BASE_URL, self.REGISTRATIONS_ENDPOINT)
        
        # Add filter for preregistrations if requested
        if filter_category:
            url = self._add_filter(url, "filter[category]", "preregistration")
        
        page = 0
        
        while url:
            # Skip collecting IDs if we haven't reached the start page
            if page < start_page:
                print(f"Skipping to page {start_page} (currently at {page})...", end=" ")
            else:
                print(f"Fetching page {page}...", end=" ")
            
            retry_count = 0
            success = False
            
            while retry_count <= max_retries and not success:
                try:
                    response = self.session.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Only extract IDs if we've reached the start page
                    if page >= start_page:
                        # Extract IDs from current page
                        page_ids = []
                        for registration in data.get("data", []):
                            reg_id = registration.get("id", "")
                            if reg_id:
                                # OSF IDs are typically in format like "abc12" or "https://osf.io/abc12/"
                                # Extract just the ID part
                                clean_id = self._extract_id(reg_id)
                                if clean_id:
                                    page_ids.append(clean_id)
                        
                        registration_ids.extend(page_ids)
                        print(f"Found {len(page_ids)} registration(s) (total: {len(registration_ids)})")
                        
                        # Check if we've reached max_results
                        if max_results and len(registration_ids) >= max_results:
                            registration_ids = registration_ids[:max_results]
                            return registration_ids
                    else:
                        print(f"Skipped (reached page {page})")
                    
                    # Get next page URL
                    url = data.get("links", {}).get("next")
                    page += 1
                    success = True
                    
                except requests.HTTPError as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"\nError fetching page {page}: {e}")
                        print(f"Retrying in {retry_wait} seconds... (attempt {retry_count}/{max_retries})")
                        time.sleep(retry_wait)
                    else:
                        print(f"\nMax retries reached for page {page}. Skipping and continuing...")
                        # Skip this page and try to get the next URL if available
                        # We'll break out of the retry loop and try to continue
                        break
                except Exception as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"\nUnexpected error: {e}")
                        print(f"Retrying in {retry_wait} seconds... (attempt {retry_count}/{max_retries})")
                        time.sleep(retry_wait)
                    else:
                        print(f"\nMax retries reached for page {page}. Skipping and continuing...")
                        break
            
            # If we exhausted retries and couldn't get the page, we need to break
            # since we don't have the next URL
            if not success:
                print(f"\nUnable to fetch page {page} after {max_retries} retries. Stopping.")
                break
        
        return registration_ids
    
    def _extract_id(self, reg_id: str) -> str:
        """
        Extract clean OSF ID from various formats.
        
        Args:
            reg_id: OSF ID in various formats (e.g., "abc12", "https://osf.io/abc12/", etc.)
        
        Returns:
            Clean OSF ID (e.g., "abc12")
        """
        # If it's a URL, extract the ID from the path
        if reg_id.startswith("http"):
            # Extract ID from URL like "https://osf.io/abc12/" or "https://api.osf.io/v2/registrations/abc12/"
            parts = reg_id.rstrip("/").split("/")
            return parts[-1] if parts else reg_id
        
        # If it's already a clean ID, return as-is
        return reg_id
    
    def _add_filter(self, url: str, filter_key: str, filter_value: str) -> str:
        """
        Add a filter parameter to a URL.
        
        Args:
            url: Base URL
            filter_key: Filter parameter name (e.g., "filter[category]")
            filter_value: Filter value
        
        Returns:
            URL with filter parameter added
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params[filter_key] = [filter_value]
        
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def save_ids(self, ids: List[str], output_file: Path) -> None:
        """
        Append IDs to a text file (one per line), avoiding duplicates.
        
        Args:
            ids: List of OSF IDs
            output_file: Path to output file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing IDs if file exists
        existing_ids = set()
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_ids = {line.strip() for line in f if line.strip()}
        
        # Filter out duplicates
        new_ids = [reg_id for reg_id in ids if reg_id not in existing_ids]
        
        # Append new IDs to file
        if new_ids:
            with open(output_file, 'a', encoding='utf-8') as f:
                for reg_id in new_ids:
                    f.write(f"{reg_id}\n")
            print(f"\nAppended {len(new_ids)} new IDs to {output_file} (skipped {len(ids) - len(new_ids)} duplicates)")
        else:
            print(f"\nNo new IDs to append (all {len(ids)} IDs already exist in {output_file})")

