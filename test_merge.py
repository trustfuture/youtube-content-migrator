#!/usr/bin/env python3

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.processor.video_processor import VideoProcessor
from src.config.settings import ConfigManager


def test_merge_functionality():
    print("Testing YouTube Content Migrator - Video Merge Functionality")
    print("=" * 60)
    
    downloads_dir = Path('./downloads/n8n')
    
    if not downloads_dir.exists():
        print(f"❌ Downloads directory not found: {downloads_dir}")
        print("Please ensure you have downloaded some videos with subtitles first.")
        return
    
    processor = VideoProcessor()
    
    print(f"🔍 Scanning for videos in: {downloads_dir}")
    video_files = processor._find_video_files(downloads_dir)
    
    if not video_files:
        print("❌ No video files found in the downloads directory.")
        return
    
    print(f"📹 Found {len(video_files)} video file(s):")
    
    for i, video_file in enumerate(video_files, 1):
        print(f"   {i}. {video_file.name}")
        
        zh_hans_subtitle = processor._find_matching_subtitle(video_file, 'zh-Hans')
        zh_hant_subtitle = processor._find_matching_subtitle(video_file, 'zh-Hant')
        en_subtitle = processor._find_matching_subtitle(video_file, 'en')
        
        print(f"      📝 zh-Hans subtitle: {'✅' if zh_hans_subtitle else '❌'}")
        if zh_hans_subtitle:
            print(f"         {zh_hans_subtitle.name}")
        
        print(f"      📝 zh-Hant subtitle: {'✅' if zh_hant_subtitle else '❌'}")
        if zh_hant_subtitle:
            print(f"         {zh_hant_subtitle.name}")
            
        print(f"      📝 English subtitle: {'✅' if en_subtitle else '❌'}")
        if en_subtitle:
            print(f"         {en_subtitle.name}")
        
        print()
    
    ready_videos = [v for v in video_files if processor._find_matching_subtitle(v, 'zh-Hans')]
    
    if ready_videos:
        print(f"🎬 {len(ready_videos)} video(s) ready for Chinese subtitle merging")
        print("\nTo merge videos with Chinese subtitles, run:")
        print(f"   python youtube-migrator.py merge {downloads_dir} --batch -l zh-Hans -o ./merged_videos")
        print("\nTo preview what would be processed:")
        print(f"   python youtube-migrator.py merge {downloads_dir} --batch -l zh-Hans --dry-run")
    else:
        print("❌ No videos with Chinese subtitles found.")
        print("Make sure to download videos with subtitle options enabled.")
    
    print("\n" + "=" * 60)
    print("Test completed! ✅")


if __name__ == "__main__":
    try:
        test_merge_functionality()
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        sys.exit(1)