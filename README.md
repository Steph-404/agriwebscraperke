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

### Basic Usage

Run the scraper with the default configuration:

```bash
python kalroscraper.py
```

### Customizing URLs

Edit the `target_urls` list in `kalroscraper.py` to add the URLs you want to download:

```python
target_urls = [
    "https://kalroerepository.kalro.org/bitstreams/45eff860-ea9e-49ca-a145-eca1389b1a5b/download",
    "https://kalroerepository.kalro.org/bitstreams/another-uuid-here/download",
    # Add more URLs here
]
```

### How It Works

1. The scraper creates a `downloads/` directory for all download-related content
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
├── kalroscraper.py              # Main scraper script
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── LICENSE                     # MIT License
├── .gitignore                  # Git ignore rules
└── downloads/                  # Downloaded files (created on first run)
    └── kalro_research_files/   # Downloaded research files
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
