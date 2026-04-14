"""
KALRO Repository URL Discovery Module

This module uses the DSpace REST API to discover download URLs
for research files from the KALRO repository.
"""

import requests
import json
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
        
        if "_embedded" in data and "searchResult" in data["_embedded"]:
            objects = data["_embedded"]["searchResult"]["_embedded"]["objects"]
            for obj in objects:
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
    
    all_urls = set()
    
    for community_name, community_uuid in communities.items():
        print(f"\n[DISCOVER] Processing community: {community_name}")
        print(f"[DISCOVER] Community UUID: {community_uuid}")
        
        # Get collections in this community
        collections = get_collections(community_uuid)
        print(f"[DISCOVER] Found {len(collections)} collections")
        
        for collection in collections:
            print(f"\n[DISCOVER] Processing collection: {collection['name']}")
            print(f"[DISCOVER] Collection UUID: {collection['uuid']}")
            
            # Get items from this collection
            items = get_items_from_collection(collection['uuid'])
            print(f"[DISCOVER] Found {len(items)} items")
            
            for item in items:
                print(f"[DISCOVER] Processing item: {item['name']}")
                
                # Get bitstreams from this item
                bitstreams = get_bitstreams_from_item(item['uuid'])
                
                for bs in bitstreams:
                    download_url = bs['download_url']
                    all_urls.add(download_url)
                    print(f"[DISCOVER] Found file: {bs['name']} ({bs['size_bytes']} bytes)")
                    print(f"[DISCOVER] Download URL: {download_url}")
    
    print(f"\n[DISCOVER] Total unique download URLs found: {len(all_urls)}")
    return all_urls


def save_urls_to_file(urls: Set[str], filename: str = "discovered_urls.txt"):
    """Save discovered URLs to a file."""
    with open(filename, 'w') as f:
        for url in sorted(urls):
            f.write(url + '\n')
    print(f"[DISCOVER] Saved {len(urls)} URLs to {filename}")


def load_urls_from_file(filename: str = "discovered_urls.txt") -> Set[str]:
    """Load discovered URLs from a file."""
    try:
        with open(filename, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


if __name__ == "__main__":
    # Discover URLs from Crops and Livestock communities
    urls = discover_download_urls()
    
    # Save to file
    save_urls_to_file(urls)
    
    print("\n[DISCOVER] Discovery complete!")
