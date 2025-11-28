"""OSF API integration for fetching preregistration data"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

from ..utils.io import save_json
from ..utils.logging import setup_logging

logger = setup_logging()


class OSFFetcher:
    """Fetcher for OSF preregistration data via API."""
    
    BASE_URL = "https://api.osf.io/v2/"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize OSF fetcher.
        
        Args:
            api_token: Optional OSF API token for authenticated requests.
        """
        self.api_token = api_token
        self.session = requests.Session()
        
        if api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {api_token}"
            })
    
    def fetch_preregistration(self, osf_id: str) -> Dict:
        """
        Fetch a single preregistration by OSF ID.
        
        Args:
            osf_id: OSF registration ID (e.g., "abc12").
        
        Returns:
            Dictionary containing preregistration metadata and content.
        """
        # Fetch registration metadata
        reg_url = urljoin(self.BASE_URL, f"registrations/{osf_id}/")
        logger.info(f"Fetching registration metadata for {osf_id}")
        
        response = self.session.get(reg_url)
        response.raise_for_status()
        reg_data = response.json()["data"]
        
        # Fetch full text from files
        files_url = reg_data["relationships"]["files"]["links"]["related"]["href"]
        logger.info(f"Fetching files for {osf_id}")
        
        files_response = self.session.get(files_url)
        files_response.raise_for_status()
        files_data = files_response.json()
        
        # Extract text from files (prioritize .txt, .md, .docx if available)
        full_text = self._extract_text_from_files(files_data)
        
        result = {
            "osf_id": osf_id,
            "metadata": reg_data,
            "full_text": full_text,
            "files_info": files_data
        }
        
        return result
    
    def _extract_text_from_files(self, files_data: Dict) -> str:
        """
        Extract text content from OSF files.
        
        Args:
            files_data: JSON response from OSF files endpoint.
        
        Returns:
            Concatenated text from all text files.
        """
        text_parts = []
        
        # Process files in the response
        for file_item in files_data.get("data", []):
            file_attrs = file_item.get("attributes", {})
            file_name = file_attrs.get("name", "")
            download_url = file_attrs.get("links", {}).get("download", "")
            
            # Prioritize text-based files
            if any(file_name.lower().endswith(ext) for ext in [".txt", ".md", ".rtf"]):
                try:
                    response = self.session.get(download_url)
                    response.raise_for_status()
                    text_content = response.text
                    text_parts.append(f"=== {file_name} ===\n{text_content}\n")
                except Exception as e:
                    logger.warning(f"Failed to fetch {file_name}: {e}")
        
        return "\n".join(text_parts) if text_parts else ""
    
    def fetch_multiple(self, osf_ids: List[str], output_dir: Path) -> List[str]:
        """
        Fetch multiple preregistrations and save to disk.
        
        Args:
            osf_ids: List of OSF registration IDs.
            output_dir: Directory to save raw JSON files.
        
        Returns:
            List of successfully fetched OSF IDs.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        successful = []
        
        for osf_id in osf_ids:
            try:
                data = self.fetch_preregistration(osf_id)
                output_path = output_dir / f"{osf_id}.json"
                save_json(data, output_path)
                successful.append(osf_id)
                logger.info(f"Saved {osf_id} to {output_path}")
            except Exception as e:
                logger.error(f"Failed to fetch {osf_id}: {e}")
        
        return successful


def fetch_from_file(input_file: Path, output_dir: Path, api_token: Optional[str] = None) -> None:
    """
    Fetch preregistrations from a file containing OSF IDs (one per line).
    
    Args:
        input_file: Path to file with OSF IDs (one per line).
        output_dir: Directory to save raw JSON files.
        api_token: Optional OSF API token.
    """
    with open(input_file, 'r') as f:
        osf_ids = [line.strip() for line in f if line.strip()]
    
    fetcher = OSFFetcher(api_token=api_token)
    successful = fetcher.fetch_multiple(osf_ids, output_dir)
    
    logger.info(f"Successfully fetched {len(successful)}/{len(osf_ids)} preregistrations")

