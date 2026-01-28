# YouTube Content Migrator

A comprehensive tool for downloading and migrating YouTube video content with metadata preservation and intelligent file organization.

## Features

- 🎥 **Video Downloads**: Download individual videos, playlists, or entire channels
- 📊 **Metadata Extraction**: Comprehensive metadata extraction including titles, descriptions, tags, and engagement metrics
- 📁 **Smart Organization**: Automatic file organization by channel, date, or custom structure
- 🔧 **Configurable**: Extensive configuration options for downloads, quality, and organization
- 📝 **Multiple Formats**: Support for various video qualities and audio-only downloads
- 🌍 **Subtitle Support**: Download subtitles in multiple languages
- 🎬 **Video Subtitle Merging**: Merge Chinese subtitles directly into videos (hardcoded subtitles)
- 📈 **Progress Tracking**: Real-time progress bars and detailed logging
- 🛠 **CLI Interface**: Powerful command-line interface for automation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd youtube-content-migrator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x youtube-migrator.py
```

## Quick Start

### Download a single video:
```bash
./youtube-migrator.py download "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download a playlist:
```bash
./youtube-migrator.py download --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Download with specific quality:
```bash
./youtube-migrator.py download -q 720p "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Extract metadata only:
```bash
./youtube-migrator.py metadata "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Merge videos with Chinese subtitles:
```bash
# Single video
./youtube-migrator.py merge "path/to/video.mp4" -l zh-Hans

# Batch process all videos in directory  
./youtube-migrator.py merge ./downloads/n8n --batch -l zh-Hans -o ./merged_videos
```

## Commands

### Download
Download YouTube videos with various options:

```bash
# Basic download
./youtube-migrator.py download URL [URL...]

# Options:
-o, --output DIR          Output directory
-q, --quality QUALITY     Video quality (best, worst, 720p, 1080p, audio)
--audio-only              Download audio only
--no-metadata             Skip metadata extraction
--no-organize             Skip file organization
--playlist                Treat URLs as playlists
--channel                 Treat URLs as channels
--limit N                 Limit number of videos to download
```

### Metadata
Extract metadata without downloading videos:

```bash
./youtube-migrator.py metadata URL [URL...]

# Options:
-o, --output DIR          Output directory for metadata
--format FORMAT           Output format (json, csv)
```

### Configuration
Manage application configuration:

```bash
# Show current configuration
./youtube-migrator.py config show

# Set configuration value
./youtube-migrator.py config set SECTION KEY VALUE

# Reset to defaults
./youtube-migrator.py config reset

# Export configuration
./youtube-migrator.py config export config.json

# Import configuration
./youtube-migrator.py config import config.json

# Validate configuration
./youtube-migrator.py config validate
```

### Organization
Organize existing files:

```bash
./youtube-migrator.py organize PATH

# Options:
-o, --output DIR          Output directory
--cleanup                 Clean up empty directories
```

### Reports
Generate reports about downloaded content:

```bash
./youtube-migrator.py report PATH

# Options:
-o, --output FILE         Output file for report
--format FORMAT           Report format (json, text)
```

### Merge
Merge videos with subtitles (hardcoded):

```bash
./youtube-migrator.py merge INPUT

# Options:
-o, --output DIR          Output directory  
-l, --lang LANG           Subtitle language (zh-Hans, zh-Hant, zh, en)
-q, --quality QUALITY     Output video quality (high, medium, low, lossless)
--fontsize SIZE           Subtitle font size (default: 24)
--fontcolor COLOR         Subtitle font color (default: white) 
--outline WIDTH           Subtitle outline thickness (default: 2)
--batch                   Process all videos in directory
--dry-run                 Show what would be processed without doing it
```

## Configuration

The tool uses a configuration file located at `~/.youtube-migrator/config.ini`. You can customize various aspects:

### Download Settings
- Output path and quality preferences
- Subtitle and thumbnail download options
- Concurrent download limits
- Rate limiting settings

### Organization Settings
- File naming templates
- Directory structure preferences
- Automatic cleanup options

### Metadata Settings
- Which metadata to extract
- Export formats
- Technical information inclusion

### Logging Settings
- Log levels and file locations
- Console output preferences
- Progress display options

## File Organization

By default, files are organized as follows:

```
downloads/
├── Channel_Name_ID/
│   ├── videos/
│   │   └── Video_Title_ID/
│   │       └── video_file.mp4
│   ├── metadata/
│   │   └── Video_Title_ID_metadata.json
│   ├── thumbnails/
│   │   └── Video_Title_ID_thumbnail.jpg
│   ├── subtitles/
│   │   └── Video_Title_ID_en.vtt
│   └── playlists/
│       └── Playlist_Name_ID/
│           └── playlist_manifest.json
```

## Output artifacts (manifests & reports)

This tool writes a few machine-readable JSON files to make migrations and auditing easier:

### Per-video manifest (`manifest.json`)
Created inside each video folder (e.g. `.../videos/<title>_<id>/manifest.json`).

Contains (stable-ish) fields like:
- `video_id`, `title`, `uploader`, `url`
- `status`: `downloaded` / `skipped` / `dry-run`
- `paths`: includes `video_dir` and (best-effort) `prepared_filename`

### Run index (`index.json`)
Created at the download output root (e.g. `./downloads/index.json`).

It lists all items processed in the run:
- `video_id`, `title`, `status`
- `video_dir` and `manifest_path`

### Run report (`report.json`)
Created at the download output root (e.g. `./downloads/report.json`).

It includes:
- `summary` (counts, skip reasons, top errors)
- the raw `results` array for debugging

## P2 download helpers

- `--dry-run`: list what would be downloaded without downloading.
  - For `--playlist` / `--channel` it lists entries (honors `--limit`).
  - For single videos it computes the target folder and writes a manifest stub.
- `--force`: bypass dedupe (redownload even if the video was already downloaded).

## Examples

### Download a channel with custom settings:
```bash
./youtube-migrator.py download \\
  --channel \\
  --limit 50 \\
  -q 1080p \\
  -o "./my_downloads" \\
  "https://www.youtube.com/c/CHANNEL_NAME"
```

### Extract metadata for multiple videos:
```bash
./youtube-migrator.py metadata \\
  --format json \\
  -o "./metadata" \\
  "https://www.youtube.com/watch?v=VIDEO1" \\
  "https://www.youtube.com/watch?v=VIDEO2"
```

### Generate a report:
```bash
./youtube-migrator.py report ./downloads --format json -o report.json
```

### Merge downloaded videos with Chinese subtitles:
```bash
# Merge all videos in the n8n directory with Chinese simplified subtitles
./youtube-migrator.py merge ./downloads/n8n --batch -l zh-Hans -q high -o ./merged_videos

# Preview what would be processed
./youtube-migrator.py merge ./downloads/n8n --batch -l zh-Hans --dry-run

# Merge single video with custom subtitle styling
./youtube-migrator.py merge "./downloads/n8n/video.mp4" -l zh-Hans --fontsize 28 --fontcolor yellow --outline 3
```

## Legal and Ethical Considerations

⚠️ **Important**: This tool is for educational and personal use only. Please ensure you comply with:

- YouTube's Terms of Service
- Copyright laws in your jurisdiction
- Fair use guidelines
- Content creators' rights

Always respect content creators and consider supporting them through official channels.

## Requirements

- Python 3.8+
- FFmpeg (required for video processing and subtitle merging)
- yt-dlp
- Other dependencies listed in `requirements.txt`

### Installing FFmpeg:

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to PATH.

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**: Ensure the script is executable and you have write permissions to the output directory.

2. **Download failures**: YouTube frequently changes its API. Update yt-dlp regularly:
   ```bash
   pip install --upgrade yt-dlp
   ```

3. **Rate limiting**: If you encounter rate limiting, reduce concurrent downloads in the configuration.

4. **Disk space**: Large channels can consume significant disk space. Monitor available space and use the `--limit` option.

### Logs

Check the log files for detailed error information:
- Default location: `./logs/youtube-migrator.log`
- Use `./youtube-migrator.py config show` to see current log file location

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.