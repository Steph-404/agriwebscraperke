import os
import requests
import re
import mimetypes
from typing import List, Tuple

# --- Configuration ---
DOWNLOAD_DIR = 'downloads/kalro_research_files'
INDEX_FILE = 'downloads/downloaded_urls_index.txt'

def setup_environment():
    """Ensure the download directory and index file exist."""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    if not os.path.exists(INDEX_FILE):
        open(INDEX_FILE, 'w').close() # Create an empty file if it doesn't exist

def load_indexed_urls():
    """Read the index file and return a set of already downloaded URLs."""
    with open(INDEX_FILE, 'r') as f:
        # Using a set makes looking up URLs incredibly fast (O(1) time complexity)
        return set(line.strip() for line in f if line.strip())

def load_discovered_urls(filename: str = 'discovered_urls.txt') -> List[Tuple[str, str]]:
    """Load URLs with their source folder paths from hierarchical folder structure.
    
    Returns:
        List of tuples (url, folder_path) where folder_path is the community/collection path.
    """
    # If a specific file is provided and exists, load from it (backward compatibility)
    if os.path.exists(filename) and filename != 'discovered_urls.txt':
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"[INFO] Loaded {len(urls)} URLs from {filename} (will save to base directory)")
        # For backward compatibility, use base download dir
        return [(url, DOWNLOAD_DIR) for url in urls]
    
    # Otherwise, scan the hierarchical folder structure for all discovered_urls.txt files
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"[INFO] No download directory found at {DOWNLOAD_DIR}")
        return []
    
    all_urls_with_paths = []
    # Walk through the directory tree
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        if 'discovered_urls.txt' in files:
            file_path = os.path.join(root, 'discovered_urls.txt')
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
                # Use the directory containing discovered_urls.txt as the download folder
                for url in urls:
                    # Transform old /download URLs to /content endpoints
                    if url.endswith('/download'):
                        url = url.replace('/download', '/content')
                        # Also ensure it uses the API base if it doesn't already
                        if '/server/api/core/bitstreams/' not in url:
                            url = url.replace('/bitstreams/', '/server/api/core/bitstreams/')
                    all_urls_with_paths.append((url, root))
            print(f"[INFO] Loaded {len(urls)} URLs from {file_path}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls_with_paths = []
    for url, folder_path in all_urls_with_paths:
        if url not in seen:
            seen.add(url)
            unique_urls_with_paths.append((url, folder_path))
    
    print(f"[INFO] Total unique URLs loaded from all collection folders: {len(unique_urls_with_paths)}")
    return unique_urls_with_paths

def mark_url_as_downloaded(url, indexed_urls):
    """Add the URL to our local set and append it to the index text file."""
    indexed_urls.add(url)
    with open(INDEX_FILE, 'a') as f:
        f.write(url + '\n')

def get_filename_from_response(response, url):
    """Attempt to get the true filename from the server headers."""
    # 1. Check Content-Disposition header (Usually contains: attachment; filename="doc.pdf")
    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition:
        # Extract filename using regex
        match = re.search(r'filename="?([^";]+)"?', content_disposition)
        if match:
            return match.group(1)
            
    # 2. Fallback if the header doesn't exist: Use the UUID from the URL + mime type
    url_parts = url.split('/')
    if len(url_parts) >= 2:
        uuid_part = url_parts[-2] # e.g., 45eff860-ea9e-49ca-a145-eca1389b1a5b
        
        # Try to guess extension based on the content type (e.g., application/pdf -> .pdf)
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        ext = mimetypes.guess_extension(content_type) or '.pdf' 
        return f"file_{uuid_part}{ext}"
        
    return "unknown_download.pdf"

def download_research_file(url, indexed_urls, folder_path=None):
    """Download the file if it hasn't been downloaded yet.
    
    Args:
        url: The download URL
        indexed_urls: Set of already downloaded URLs
        folder_path: Optional path to save the file (defaults to DOWNLOAD_DIR)
    """
    # Check if we already have it
    if url in indexed_urls:
        print(f"[SKIPPED] Already downloaded: {url}")
        return

    # Use provided folder_path or default to DOWNLOAD_DIR
    target_folder = folder_path if folder_path else DOWNLOAD_DIR
    
    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)

    print(f"[DOWNLOADING] Starting download for: {url}")
    try:
        # stream=True prevents loading massive files into your computer's RAM all at once
        with requests.get(url, stream=True, timeout=30) as response:
            # Log response details for debugging
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            # Raise an error if the URL is broken (e.g., 404 Not Found)
            response.raise_for_status()
            
            # Determine what to name the file
            filename = get_filename_from_response(response, url)
            
            # Remove any unsafe characters from the filename just in case
            filename = "".join(c for c in filename if c.isalnum() or c in " ._-")
            filepath = os.path.join(target_folder, filename)
            
            # Write the file in chunks
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1048576):
                    if chunk:
                        f.write(chunk)
                        
            print(f"[SUCCESS] Saved to: {filepath}")
            
            # Success! Now record this URL so we never download it again
            mark_url_as_downloaded(url, indexed_urls)

    except requests.exceptions.HTTPError as e:
        # Log detailed error information
        print(f"[ERROR] HTTP Error for {url}")
        print(f"[ERROR] Status code: {e.response.status_code}")
        print(f"[ERROR] Response headers: {dict(e.response.headers)}")
        try:
            print(f"[ERROR] Response body (first 500 chars): {e.response.text[:500]}")
        except:
            print(f"[ERROR] Could not read response body")
        print(f"[ERROR] Full error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download {url}. Error: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Setup folders and files
    setup_environment()
    
    # 2. Load memory of what we've already done
    indexed_urls = load_indexed_urls()
    
    # 3. Load URLs - either from discovered_urls.txt or use manual list
    discovered_urls = load_discovered_urls()
    
    if discovered_urls:
        # Use URLs discovered by the discovery module
        target_urls = discovered_urls
        print(f"[INFO] Using {len(target_urls)} URLs from discovery module")
        
        # Check if URLs are in tuple format (url, folder_path) or just URLs
        if target_urls and isinstance(target_urls[0], tuple):
            # URLs with folder paths - hierarchical structure
            for url, folder_path in target_urls:
                download_research_file(url, indexed_urls, folder_path)
        else:
            # Just URLs - backward compatibility
            for target in target_urls:
                download_research_file(target, indexed_urls)
    else:
        # Fallback to manual list
        target_urls = [
            "https://kalroerepository.kalro.org/bitstreams/45eff860-ea9e-49ca-a145-eca1389b1a5b/download",
            # You can add more URLs here, e.g.:
            # "https://kalroerepository.kalro.org/bitstreams/another-uuid-here/download"
        ]
        print(f"[INFO] Using {len(target_urls)} manually specified URLs")
        
        # 4. Loop through and download
        for target in target_urls:
            download_research_file(target, indexed_urls)
        
    print("\nBatch processing complete.")