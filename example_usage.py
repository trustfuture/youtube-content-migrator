#!/usr/bin/env python3
"""
YouTube Content Migrator - Video Subtitle Merging Examples

This script demonstrates how to use the video subtitle merging functionality.
"""

import sys
import os
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def main():
    print("🎬 YouTube Content Migrator - Video Subtitle Merging Examples")
    
    # Check if download directory exists
    downloads_dir = Path("./downloads/n8n")
    if not downloads_dir.exists():
        print(f"\n❌ Downloads directory not found: {downloads_dir}")
        print("Please run some downloads first using:")
        print("   uv run python youtube-migrator.py download 'YOUTUBE_URL' --audio-only")
        return

    print_section("Available Commands")
    
    print("1. 📋 Preview what will be processed:")
    print("   uv run python youtube-migrator.py merge downloads/n8n --batch -l zh-Hans --dry-run")
    
    print("\n2. 🎯 Merge single video with Chinese simplified subtitles:")
    print("   uv run python youtube-migrator.py merge \"downloads/n8n/video.mp4\" -l zh-Hans")
    
    print("\n3. 🔄 Batch process all videos with Chinese subtitles:")
    print("   uv run python youtube-migrator.py merge downloads/n8n --batch -l zh-Hans -o ./chinese_videos")
    
    print("\n4. 🎨 Custom styling - yellow subtitles, larger font:")
    print("   uv run python youtube-migrator.py merge \"video.mp4\" -l zh-Hans --fontcolor yellow --fontsize 28")
    
    print("\n5. 📺 Different quality settings:")
    print("   uv run python youtube-migrator.py merge \"video.mp4\" -l zh-Hans -q medium")
    
    print_section("Supported Languages")
    print("• zh-Hans  - Chinese Simplified (简体中文)")
    print("• zh-Hant  - Chinese Traditional (繁體中文)")  
    print("• zh       - Chinese (auto-detect)")
    print("• en       - English")
    
    print_section("Quality Options")
    print("• high     - High quality (5000k bitrate)")
    print("• medium   - Medium quality (2500k bitrate)")
    print("• low      - Low quality (1000k bitrate)")
    print("• lossless - Best quality (no re-encoding)")
    
    print_section("Subtitle Styling Options")
    print("• --fontsize SIZE     - Font size (default: 24)")
    print("• --fontcolor COLOR   - Font color (white, yellow, red, etc.)")
    print("• --outline WIDTH     - Outline thickness (default: 2)")
    
    print_section("Current Status")
    
    # Check what's available
    video_files = list(downloads_dir.glob("*.mp4"))
    subtitle_files = list(downloads_dir.glob("*.vtt"))
    
    print(f"📹 Video files found: {len(video_files)}")
    for video in video_files:
        print(f"   • {video.name}")
    
    print(f"\n📝 Subtitle files found: {len(subtitle_files)}")
    for subtitle in subtitle_files:
        print(f"   • {subtitle.name}")
    
    if video_files:
        print(f"\n✅ Ready to merge! Try running:")
        print(f"   uv run python youtube-migrator.py merge downloads/n8n --batch -l zh-Hans --dry-run")
    else:
        print(f"\n📥 No videos found. Download some first!")
    
    print_section("Configuration")
    print("You can also customize default settings:")
    print("   uv run python youtube-migrator.py config show")
    print("   uv run python youtube-migrator.py config set video_processing default_subtitle_language zh-Hans")
    
    print(f"\n🎉 Happy video merging!")


if __name__ == "__main__":
    main()