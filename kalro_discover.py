"""
KALRO Repository URL Discovery Module

This module uses the DSpace REST API to discover download URLs
for research files from the KALRO repository.
"""

import requests
import json
import os
from typing import List, Dict, Set
from urllib.parse import quote

# --- Configuration ---
BASE_URL = "https://kalroerepository.kalro.org"
API_BASE = f"{BASE_URL}/server/api/core"
DISCOVER_API = f"{BASE_URL}/server/api/discover/search/objects"

# Target Communities
COMMUNITIES = {
    "crops": "17bea01f-72da-4160-a98a-a57196e515f3",
    "livestock": "9a211b88-8884-4547-90dc-9e4dd7f696f5"
}

# Base download directory (same as kalroscraper.py)
DOWNLOAD_DIR = 'downloads/kalro_research_files'


def sanitize_folder_name(name: str) -> str:
    """Sanitize folder name to remove invalid characters."""
    # Remove or replace characters that are invalid in folder names
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def create_collection_folder(community_name: str, collection_name: str) -> str:
    """Create hierarchical folder structure for a collection."""
    # Sanitize names
    safe_community = sanitize_folder_name(community_name)
    safe_collection = sanitize_folder_name(collection_name)
    
    # Create path: downloads/kalro_research_files/community/collection
    collection_path = os.path.join(DOWNLOAD_DIR, safe_community, safe_collection)
    
    # Create directories if they don't exist
    os.makedirs(collection_path, exist_ok=True)
    
    return collection_path


def append_url_to_file(url: str, file_path: str):
    """Append a single URL to the specified file."""
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(url + '\n')


def get_collections(community_uuid: str) -> List[Dict]:
    """Get all collections within a community using the discover API."""
    collections = []
    
    try:
        # Use the discover API to search for collections within the community scope
        # This is the correct way to get collections in DSpace 7 REST API
        search_url = f"{DISCOVER_API}?query=*&dsoType=COLLECTION&scope={community_uuid}"
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "_embedded" in data and "searchResult" in data["_embedded"]:
            objects = data["_embedded"]["searchResult"]["_embedded"]["objects"]
            for obj in objects:
                collection = obj["_embedded"]["indexableObject"]
                collections.append({
                    "uuid": collection["uuid"],
                    "name": collection["name"],
                    "handle": collection.get("handle", "")
                })
        
        # Check if there are more pages
        if "page" in data:
            total_pages = data["page"].get("totalPages", 1)
            current_page = data["page"].get("number", 0)
            
            if current_page < total_pages - 1:
                # Recursively get collections from next page
                more_collections = get_collections_paginated(community_uuid, current_page + 1)
                collections.extend(more_collections)
        
        return collections
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get collections for community {community_uuid}: {e}")
        return []


def get_collections_paginated(community_uuid: str, page: int = 0, size: int = 100) -> List[Dict]:
    """Helper function to get collections from a specific page."""
    collections = []
    
    try:
        search_url = f"{DISCOVER_API}?query=*&dsoType=COLLECTION&scope={community_uuid}&page={page}&size={size}"
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "_embedded" in data and "searchResult" in data["_embedded"]:
            objects = data["_embedded"]["searchResult"]["_embedded"]["objects"]
            for obj in objects:
                collection = obj["_embedded"]["indexableObject"]
                collections.append({
                    "uuid": collection["uuid"],
                    "name": collection["name"],
                    "handle": collection.get("handle", "")
                })
        
        # Check if there are more pages
        if "page" in data:
            total_pages = data["page"].get("totalPages", 1)
            current_page = data["page"].get("number", 0)
            
            if current_page < total_pages - 1:
                # Recursively get collections from next page
                more_collections = get_collections_paginated(community_uuid, current_page + 1, size)
                collections.extend(more_collections)
        
        return collections
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get collections page {page} for community {community_uuid}: {e}")
        return []


def get_items_from_collection(collection_uuid: str, page: int = 0, size: int = 100) -> List[Dict]:
    """Get items from a collection using the discover API."""
    items = []
    
    try:
        url = f"{DISCOVER_API}?query=*&dsoType=ITEM&scope={collection_uuid}&page={page}&size={size}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Debug: print the response structure if there's an issue
        if "_embedded" not in data:
            print(f"[DEBUG] No _embedded in response for collection {collection_uuid}")
            print(f"[DEBUG] Response keys: {data.keys()}")
            return items
        
        if "searchResult" not in data["_embedded"]:
            print(f"[DEBUG] No searchResult in _embedded for collection {collection_uuid}")
            return items
        
        search_result = data["_embedded"]["searchResult"]
        
        if "_embedded" not in search_result:
            print(f"[DEBUG] No _embedded in searchResult for collection {collection_uuid}")
            return items
        
        if "objects" not in search_result["_embedded"]:
            print(f"[DEBUG] No objects in searchResult._embedded for collection {collection_uuid}")
            return items
        
        objects = search_result["_embedded"]["objects"]
        for obj in objects:
            if "_embedded" not in obj:
                print(f"[DEBUG] No _embedded in object for collection {collection_uuid}")
                continue
            
            if "indexableObject" not in obj["_embedded"]:
                print(f"[DEBUG] No indexableObject in object._embedded for collection {collection_uuid}")
                continue
            
            item = obj["_embedded"]["indexableObject"]
            items.append({
                "uuid": item["uuid"],
                "name": item["name"],
                "handle": item.get("handle", ""),
                "metadata": item.get("metadata", {})
            })
        
        # Check if there are more pages
        if "page" in data:
            total_pages = data["page"].get("totalPages", 1)
            current_page = data["page"].get("number", 0)
            
            if current_page < total_pages - 1:
                # Recursively get items from next page
                more_items = get_items_from_collection(collection_uuid, current_page + 1, size)
                items.extend(more_items)
        
        return items
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get items from collection {collection_uuid}: {e}")
        return []
    except KeyError as e:
        print(f"[ERROR] KeyError in get_items_from_collection for {collection_uuid}: {e}")
        return []


def get_bitstreams_from_item(item_uuid: str) -> List[Dict]:
    """Get all bitstreams (files) from an item."""
    bitstreams = []
    
    try:
        # Get bundles for the item
        bundles_url = f"{API_BASE}/items/{item_uuid}/bundles"
        response = requests.get(bundles_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "_embedded" in data and "bundles" in data["_embedded"]:
            for bundle in data["_embedded"]["bundles"]:
                # We only want the ORIGINAL bundle (contains the actual file)
                if bundle["name"] == "ORIGINAL":
                    bitstreams_url = bundle["_links"]["bitstreams"]["href"]
                    bitstreams_response = requests.get(bitstreams_url, timeout=30)
                    bitstreams_response.raise_for_status()
                    bitstreams_data = bitstreams_response.json()
                    
                    if "_embedded" in bitstreams_data and "bitstreams" in bitstreams_data["_embedded"]:
                        for bs in bitstreams_data["_embedded"]["bitstreams"]:
                            # Construct the download URL
                            bs_uuid = bs["uuid"]
                            download_url = f"{BASE_URL}/bitstreams/{bs_uuid}/download"
                            
                            bitstreams.append({
                                "uuid": bs["uuid"],
                                "name": bs["name"],
                                "size_bytes": bs.get("sizeBytes", 0),
                                "download_url": download_url,
                                "checksum": bs.get("checkSum", {}).get("value", ""),
                                "bundle_name": bundle["name"]
                            })
        
        return bitstreams
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get bitstreams from item {item_uuid}: {e}")
        return []


def discover_download_urls(communities: Dict[str, str] = None) -> Set[str]:
    """
    Discover all download URLs from specified communities.
    
    Args:
        communities: Dictionary mapping community names to their UUIDs.
                     If None, uses default Crops and Livestock communities.
    
    Returns:
        Set of download URLs
    """
    if communities is None:
        communities = COMMUNITIES
    
    # Create base download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    all_urls = set()
    
    for community_name, community_uuid in communities.items():
        print(f"\n{'='*60}")
        print(f"[DISCOVER] Processing community: {community_name}")
        print(f"[DISCOVER] Community UUID: {community_uuid}")
        print(f"{'='*60}")
        
        # Get collections in this community
        collections = get_collections(community_uuid)
        print(f"[DISCOVER] Found {len(collections)} collections in this community\n")
        
        for idx, collection in enumerate(collections, 1):
            print(f"\n{'='*60}")
            print(f"[DISCOVER] Collection {idx}/{len(collections)}: {collection['name']}")
            print(f"[DISCOVER] Collection UUID: {collection['uuid']}")
            print(f"{'='*60}")
            
            # Create hierarchical folder for this collection
            collection_path = create_collection_folder(community_name, collection['name'])
            print(f"[DISCOVER] Created folder: {collection_path}")
            
            # Create collection-specific discovered URLs file
            discovered_urls_file = os.path.join(collection_path, 'discovered_urls.txt')
            
            # Load existing URLs for this collection to avoid duplicates
            existing_urls = load_urls_from_file(discovered_urls_file)
            
            # Get items from this collection
            items = get_items_from_collection(collection['uuid'])
            print(f"[DISCOVER] Found {len(items)} items in this collection")
            print(f"[DISCOVER] Found {len(existing_urls)} existing URLs in this collection")
            
            # Check if collection is already complete
            if len(existing_urls) >= len(items):
                print(f"[DISCOVER] ✓ Collection already complete ({len(existing_urls)} URLs for {len(items)} items)")
                print(f"[DISCOVER] Skipping this collection...")
                # Add existing URLs to all_urls
                all_urls.update(existing_urls)
                continue
            
            urls_found_this_run = 0
            
            for item in items:
                print(f"[DISCOVER] Processing item: {item['name']}")
                
                # Get bitstreams from this item
                bitstreams = get_bitstreams_from_item(item['uuid'])
                
                for bs in bitstreams:
                    download_url = bs['download_url']
                    
                    # Only add and save if this is a new URL
                    if download_url not in existing_urls:
                        existing_urls.add(download_url)
                        all_urls.add(download_url)
                        append_url_to_file(download_url, discovered_urls_file)
                        urls_found_this_run += 1
                        print(f"[DISCOVER] Found NEW file: {bs['name']} ({bs['size_bytes']} bytes)")
                        print(f"[DISCOVER] Download URL: {download_url}")
                    else:
                        print(f"[DISCOVER] Skipping duplicate: {bs['name']}")
            
            # Report progress for this collection
            print(f"\n[DISCOVER] Collection Summary:")
            print(f"[DISCOVER]   Total items: {len(items)}")
            print(f"[DISCOVER]   Total URLs in file: {len(existing_urls)}")
            print(f"[DISCOVER]   New URLs this run: {urls_found_this_run}")
            print(f"[DISCOVER]   URLs saved to: {discovered_urls_file}")
            
            # Check if collection is complete
            if len(existing_urls) >= len(items):
                print(f"[DISCOVER] Collection complete ({len(existing_urls)} URLs for {len(items)} items)")
            else:
                print(f"[DISCOVER] Collection incomplete ({len(existing_urls)} URLs for {len(items)} items)")
    
    print(f"\n{'='*60}")
    print(f"[DISCOVER] Discovery complete!")
    print(f"[DISCOVER] Total unique download URLs across all collections: {len(all_urls)}")
    print(f"{'='*60}")
    return all_urls


def load_urls_from_file(filename: str = "discovered_urls.txt") -> Set[str]:
    """Load discovered URLs from a file."""
    try:
        with open(filename, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


if __name__ == "__main__":
    # Discover URLs from Crops and Livestock communities
    # URLs are written to collection-specific files incrementally during discovery
    urls = discover_download_urls()
    
    print("\n[DISCOVER] All discovery complete!")
