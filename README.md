# AgriWebScraperKE

A Python-based web scraper for downloading research files from the Kenya Agricultural and Livestock Research Organization (KALRO) repository.

## Overview

This project provides a simple, efficient tool to download research documents and files from the KALRO digital repository at https://kalroerepository.kalro.org/home.

## Features

- **Streaming Downloads**: Efficiently handles large files without loading them entirely into memory
- **Deduplication**: Tracks downloaded URLs to prevent redundant downloads
- **Smart Filename Extraction**: Automatically determines filenames from server headers or URL structure
- **Error Handling**: Robust error handling for network issues and invalid URLs
- **Batch Processing**: Download multiple files in sequence
- **Resume Capability**: Skip already downloaded files on subsequent runs

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Steph-404/agriwebscraperke.git
cd agriwebscraperke
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Discover Download URLs (Optional)

To automatically discover all download URLs from the KALRO repository:

```bash
python kalro_discover.py
```

This will:
- Create hierarchical folder structure: `downloads/kalro_research_files/{community}/{collection}/`
- Scan the Crops and Livestock communities
- Discover all collections within those communities
- Find all items in each collection
- Extract bitstream download URLs for each item
- Save URLs to collection-specific `discovered_urls.txt` files incrementally
- Track progress: items found vs URLs saved
- Skip collections that are already complete
- Continue automatically through all communities and collections

**Folder Structure Example:**
```
downloads/kalro_research_files/
├── crops/
│   ├── Pests and Diseases/
│   │   └── discovered_urls.txt
│   └── Cereals/
│       └── discovered_urls.txt
└── livestock/
    └── Dairy/
        └── discovered_urls.txt
```

You can customize which communities to scan by modifying the `COMMUNITIES` dictionary in `kalro_discover.py`.

### Step 2: Download Files

Run the scraper to download files:

```bash
python kalroscraper.py
```

The scraper will:
- Check for `discovered_urls.txt` and use those URLs if available
- Fall back to manually specified URLs if no discovery file exists
- Download files to `downloads/kalro_research_files/`
- Track downloaded URLs to avoid duplicates

### Basic Usage (Manual URLs)

If you prefer to specify URLs manually, edit the `target_urls` list in `kalroscraper.py`:

```python
target_urls = [
    "https://kalroerepository.kalro.org/bitstreams/45eff860-ea9e-49ca-a145-eca1389b1a5b/download",
    "https://kalroerepository.kalro.org/bitstreams/another-uuid-here/download",
]
```

### How It Works

**URL Discovery (kalro_discover.py):**
1. Connects to the KALRO DSpace REST API
2. Scans specified communities (Crops, Livestock by default)
3. Creates hierarchical folder structure: `downloads/kalro_research_files/{community}/{collection}/`
4. Retrieves all collections within each community
5. Checks if collection is already complete (skips if yes)
6. Discovers all items in each collection using pagination
7. Extracts bitstream (file) information from each item
8. Constructs download URLs for all files
9. Saves URLs to collection-specific `discovered_urls.txt` files incrementally
10. Tracks progress: items found vs URLs saved per collection
11. Continues automatically through all communities and collections
12. Marks collection as complete when URLs count matches items count

**File Download (kalroscraper.py):**
1. The scraper scans the hierarchical folder structure for all `discovered_urls.txt` files
2. It creates `downloads/kalro_research_files/` for the actual downloaded files
3. It maintains `downloads/downloaded_urls_index.txt` to track downloaded URLs
4. For each URL:
   - Checks if already downloaded (skips if yes)
   - Downloads the file using streaming (1MB chunks)
   - Extracts the filename from headers or constructs from UUID
   - Saves to the download directory
   - Records the URL in the index

## Project Structure

```
agriwebscraperke/
├── kalroscraper.py              # Main downloader script
├── kalro_discover.py            # URL discovery module (uses DSpace REST API)
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── LICENSE                     # MIT License
├── .gitignore                  # Git ignore rules
└── downloads/                  # Downloaded files (created on first run)
    └── kalro_research_files/   # Downloaded research files
        ├── crops/               # Crops community folder
        │   ├── Pests and Diseases/
        │   │   ├── discovered_urls.txt  # URLs for this collection
        │   │   └── [downloaded files]
        │   └── [other collections...]
        ├── livestock/           # Livestock community folder
        │   └── [collections...]
        └── downloaded_urls_index.txt # Index of downloaded URLs
```

## Dependencies

- `requests>=2.31.0` - HTTP library for downloading files

## Configuration

You can modify these constants in `kalroscraper.py`:

- `DOWNLOAD_DIR`: Directory for downloaded files (default: `downloads/kalro_research_files`)
- `INDEX_FILE`: File tracking downloaded URLs (default: `downloads/downloaded_urls_index.txt`)
- `timeout`: Request timeout in seconds (default: 30)
- `chunk_size`: Download chunk size in bytes (default: 1048576 / 1MB)

## Error Handling

The scraper handles various error conditions:
- Network timeouts
- Invalid URLs (404, 500, etc.)
- Connection errors
- File system errors

Errors are logged to console with descriptive messages.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for educational and research purposes. Please respect the KALRO repository's terms of service and usage policies when downloading content.

## Contact

For issues, questions, or suggestions, please open an issue on GitHub.
