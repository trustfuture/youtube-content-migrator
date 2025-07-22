#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.processor.video_processor import SubtitleConverter


def test_subtitle_conversion():
    print("Testing Subtitle Conversion")
    print("=" * 40)
    
    converter = SubtitleConverter()
    
    vtt_file = "downloads/n8n/n8n Beginner Course (1⧸9) - Introduction to Automation.zh-Hans.vtt"
    srt_file = "test_output.srt"
    
    if not Path(vtt_file).exists():
        print(f"❌ VTT file not found: {vtt_file}")
        return
    
    print(f"🔄 Converting {vtt_file}")
    
    success = converter.vtt_to_srt(vtt_file, srt_file)
    
    if success:
        print(f"✅ Conversion successful: {srt_file}")
        
        # Read and display first few lines of the SRT file
        with open(srt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print("\n📝 First 20 lines of converted SRT:")
        print("-" * 40)
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:2d}: {line.rstrip()}")
        
        print(f"\n📊 Total lines in SRT: {len(lines)}")
        
        # Clean up
        Path(srt_file).unlink()
        print(f"🗑️  Cleaned up test file: {srt_file}")
        
    else:
        print("❌ Conversion failed")


if __name__ == "__main__":
    test_subtitle_conversion()