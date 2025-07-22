# Usage Guide

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Internet connection

### Installation Steps

1. **Clone or download the project**:
   ```bash
   cd youtube-content-migrator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Make executable** (Linux/Mac):
   ```bash
   chmod +x youtube-migrator.py
   ```

4. **Verify installation**:
   ```bash
   ./youtube-migrator.py --help
   ```

## Basic Usage

### Download a Single Video

```bash
# Basic download
./youtube-migrator.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# With custom output directory
./youtube-migrator.py download -o "./my_videos" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Specific quality
./youtube-migrator.py download -q 720p "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Audio only
./youtube-migrator.py download --audio-only "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Download Playlists

```bash
# Download entire playlist
./youtube-migrator.py download --playlist "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLviYrk-U8MVGx_PSmG"

# Limit number of videos
./youtube-migrator.py download --playlist --limit 10 "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLviYrk-U8MVGx_PSmG"

# High quality with metadata
./youtube-migrator.py download --playlist -q 1080p "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLviYrk-U8MVGx_PSmG"
```

### Download Channels

```bash
# Download latest videos from channel
./youtube-migrator.py download --channel --limit 20 "https://www.youtube.com/c/channelname"

# Download all videos (use with caution)
./youtube-migrator.py download --channel "https://www.youtube.com/c/channelname"
```

## Advanced Usage

### Metadata-Only Operations

```bash
# Extract metadata without downloading
./youtube-migrator.py metadata "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Multiple videos
./youtube-migrator.py metadata \\
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \\
  "https://www.youtube.com/watch?v=oHg5SJYRHA0"

# Custom output directory
./youtube-migrator.py metadata -o "./video_metadata" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Batch Operations

```bash
# Create a file with URLs (one per line)
echo "https://www.youtube.com/watch?v=dQw4w9WgXcQ" > urls.txt
echo "https://www.youtube.com/watch?v=oHg5SJYRHA0" >> urls.txt

# Download all URLs
./youtube-migrator.py download $(cat urls.txt)
```

### Custom Configuration

```bash
# View current configuration
./youtube-migrator.py config show

# Set custom output directory
./youtube-migrator.py config set download output_path "/path/to/downloads"

# Set default quality
./youtube-migrator.py config set download quality "1080p"

# Enable subtitle downloads
./youtube-migrator.py config set download download_subtitles true

# Set subtitle languages
./youtube-migrator.py config set download subtitle_languages "en,es,fr,de"
```

### File Organization

```bash
# Organize existing files
./youtube-migrator.py organize "./messy_downloads" -o "./organized_downloads"

# Clean up empty directories
./youtube-migrator.py organize "./downloads" --cleanup

# Generate directory report
./youtube-migrator.py report "./downloads"

# Export report to JSON
./youtube-migrator.py report "./downloads" --format json -o report.json
```

## Quality Options

| Option | Description |
|--------|-------------|
| `best` | Best available quality (default) |
| `worst` | Lowest available quality |
| `720p` | 720p resolution or lower |
| `1080p` | 1080p resolution or lower |
| `audio` | Audio only (no video) |

## Configuration Sections

### Download Configuration
```bash
# Set output directory
./youtube-migrator.py config set download output_path "./my_downloads"

# Set default quality
./youtube-migrator.py config set download quality "best"

# Enable/disable subtitles
./youtube-migrator.py config set download download_subtitles true

# Set concurrent downloads
./youtube-migrator.py config set download concurrent_downloads 2
```

### Organization Configuration
```bash
# Enable channel-based organization
./youtube-migrator.py config set organization organize_by_channel true

# Custom filename template
./youtube-migrator.py config set organization filename_template "%(uploader)s - %(title)s.%(ext)s"

# Enable automatic cleanup
./youtube-migrator.py config set organization cleanup_empty_dirs true
```

### Metadata Configuration
```bash
# Include technical information
./youtube-migrator.py config set metadata include_technical_info true

# Include engagement metrics
./youtube-migrator.py config set metadata include_engagement_metrics true

# Set export format
./youtube-migrator.py config set metadata export_format "json"
```

## Output Structure

### Default Organization
```
downloads/
├── Channel_Name_ID/
│   ├── videos/
│   │   ├── Video_Title_ID/
│   │   │   └── video.mp4
│   │   └── Another_Video_ID/
│   │       └── video.mp4
│   ├── metadata/
│   │   ├── Video_Title_ID_metadata.json
│   │   └── Another_Video_ID_metadata.json
│   ├── thumbnails/
│   │   ├── Video_Title_ID_thumbnail.jpg
│   │   └── Another_Video_ID_thumbnail.jpg
│   ├── subtitles/
│   │   ├── Video_Title_ID_en.vtt
│   │   └── Video_Title_ID_es.vtt
│   └── playlists/
│       └── Playlist_Name_ID/
│           ├── playlist_manifest.json
│           └── videos/
```

### Metadata Structure
```json
{
  "basic_info": {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "description": "Official video description...",
    "uploader": "RickAstleyVEVO",
    "uploader_id": "RickAstleyVEVO",
    "channel": "RickAstleyVEVO"
  },
  "technical_info": {
    "duration": 212,
    "width": 1920,
    "height": 1080,
    "fps": 25
  },
  "engagement_metrics": {
    "view_count": 1000000000,
    "like_count": 10000000,
    "comment_count": 2000000
  },
  "timestamps": {
    "upload_date": "20091024",
    "timestamp": 1256342400
  }
}
```

## Error Handling

### Common Issues and Solutions

1. **Video unavailable**:
   ```bash
   # Skip unavailable videos
   ./youtube-migrator.py config set advanced skip_unavailable true
   ```

2. **Rate limiting**:
   ```bash
   # Reduce concurrent downloads
   ./youtube-migrator.py config set download concurrent_downloads 1
   
   # Add rate limiting
   ./youtube-migrator.py config set download rate_limit "100K"
   ```

3. **Disk space issues**:
   ```bash
   # Use lower quality
   ./youtube-migrator.py download -q worst URL
   
   # Audio only for large batches
   ./youtube-migrator.py download --audio-only --playlist URL
   ```

4. **Permission errors**:
   ```bash
   # Check output directory permissions
   ls -la ./downloads
   
   # Use different output directory
   ./youtube-migrator.py download -o ~/Documents/youtube URL
   ```

### Logging and Debugging

```bash
# Enable debug logging
./youtube-migrator.py config set logging level DEBUG

# Check log file location
./youtube-migrator.py config show | grep log_file

# View recent logs
tail -f ./logs/youtube-migrator.log
```

## Tips and Best Practices

### Performance Optimization
- Use lower quality for large batches
- Limit concurrent downloads on slower connections
- Use `--limit` for channel downloads
- Enable rate limiting for stable downloads

### Storage Management
- Regularly clean up with `organize --cleanup`
- Monitor disk space for large operations
- Use external storage for large collections
- Consider audio-only for music content

### Metadata Preservation
- Always keep metadata files with videos
- Export metadata before major reorganization
- Use JSON format for better compatibility
- Include engagement metrics for analytics

### Automation
- Create shell scripts for regular downloads
- Use configuration files for different scenarios
- Set up cron jobs for periodic updates
- Maintain URL lists for batch processing

## Legal and Ethical Guidelines

### Compliance
- Respect YouTube's Terms of Service
- Follow copyright laws in your jurisdiction
- Use content for personal/educational purposes only
- Don't redistribute downloaded content

### Best Practices
- Support creators through official channels
- Use reasonable download limits
- Respect rate limiting
- Give attribution when using content legally

### Rate Limiting
- Don't overwhelm YouTube's servers
- Use built-in rate limiting features
- Space out large downloads
- Monitor for 429 (rate limited) responses