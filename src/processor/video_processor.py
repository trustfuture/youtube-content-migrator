import os
import re
import logging
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import ffmpeg
from tqdm import tqdm


class SubtitleConverter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def vtt_to_srt(self, vtt_file: str, srt_file: str) -> bool:
        try:
            with open(vtt_file, 'r', encoding='utf-8') as f:
                vtt_content = f.read()

            srt_content = self._convert_vtt_to_srt_content(vtt_content)
            
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            self.logger.info(f"Converted VTT to SRT: {vtt_file} -> {srt_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to convert VTT to SRT: {str(e)}")
            return False

    def _convert_vtt_to_srt_content(self, vtt_content: str) -> str:
        lines = vtt_content.split('\n')
        srt_lines = []
        subtitle_index = 1
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if '-->' in line:
                timestamp = self._convert_vtt_timestamp_to_srt(line)
                
                # Skip very short durations (less than 0.1 seconds)
                if not self._is_valid_duration(line):
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        i += 1
                    continue
                
                i += 1
                subtitle_text = []
                
                while i < len(lines) and lines[i].strip():
                    text = lines[i].strip()
                    if text and not text.startswith('NOTE') and not text.startswith('Kind:') and not text.startswith('Language:'):
                        cleaned_text = self._clean_subtitle_text(text)
                        if cleaned_text and not self._is_duplicate_line(cleaned_text, subtitle_text):
                            subtitle_text.append(cleaned_text)
                    i += 1
                
                if subtitle_text and any(len(text.strip()) > 1 for text in subtitle_text):
                    srt_lines.append(str(subtitle_index))
                    srt_lines.append(timestamp)
                    srt_lines.extend(subtitle_text)
                    srt_lines.append('')
                    subtitle_index += 1
            
            i += 1
        
        return '\n'.join(srt_lines)

    def _convert_vtt_timestamp_to_srt(self, vtt_timestamp: str) -> str:
        vtt_timestamp = re.sub(r'align:.*', '', vtt_timestamp).strip()
        return vtt_timestamp.replace('.', ',')

    def _clean_subtitle_text(self, text: str) -> str:
        # Remove HTML/XML tags including timing tags like <00:00:01.189><c>
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'&lt;[^&]*&gt;', '', text)
        
        # Remove timing information like <00:00:01.189>
        text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text)
        
        # Remove align and position attributes
        text = re.sub(r'align:\w+', '', text)
        text = re.sub(r'position:\d+%', '', text)
        
        # Clean HTML entities
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _is_duplicate_line(self, new_text: str, existing_lines: List[str]) -> bool:
        """Check if the new text is a duplicate or subset of existing lines"""
        if not new_text:
            return True
            
        for existing in existing_lines:
            if new_text == existing or new_text in existing or existing in new_text:
                return True
        return False

    def _is_valid_duration(self, timestamp_line: str) -> bool:
        """Check if the subtitle duration is long enough to be useful"""
        try:
            # Extract start and end times
            times = timestamp_line.split('-->')
            if len(times) != 2:
                return False
            
            start_time = times[0].strip().split()[0]  # Remove align/position info
            end_time = times[1].strip().split()[0]
            
            # Convert to seconds
            def time_to_seconds(time_str):
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            
            duration = end_seconds - start_seconds
            
            # Filter out very short durations (less than 0.1 seconds)
            return duration >= 0.1
            
        except Exception:
            return True  # If we can't parse, include it to be safe


class VideoProcessor:
    def __init__(self, temp_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.subtitle_converter = SubtitleConverter()
        
        self.default_subtitle_style = {
            'fontsize': 24,
            'fontcolor': 'white',
            'outline': 2,
            'outlinecolor': 'black',
            'shadow': 1,
            'shadowcolor': 'black',
            'shadowx': 1,
            'shadowy': 1,
            'fontname': 'Arial'
        }

    def merge_video_with_subtitles(self, 
                                 video_path: str, 
                                 subtitle_path: str, 
                                 output_path: str,
                                 subtitle_style: Optional[Dict] = None,
                                 video_quality: str = 'high') -> Dict[str, Any]:
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            if not os.path.exists(subtitle_path):
                raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            srt_path = self._ensure_srt_format(subtitle_path)
            
            style = {**self.default_subtitle_style, **(subtitle_style or {})}
            
            result = self._merge_with_ffmpeg(video_path, srt_path, output_path, style, video_quality)
            
            if srt_path != subtitle_path and os.path.exists(srt_path):
                os.remove(srt_path)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to merge video with subtitles: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'video_path': video_path,
                'subtitle_path': subtitle_path
            }

    def _ensure_srt_format(self, subtitle_path: str) -> str:
        if subtitle_path.endswith('.vtt'):
            srt_path = os.path.join(
                self.temp_dir, 
                f"temp_subtitle_{os.getpid()}.srt"
            )
            
            if self.subtitle_converter.vtt_to_srt(subtitle_path, srt_path):
                return srt_path
            else:
                raise Exception("Failed to convert VTT to SRT format")
        
        return subtitle_path

    def _merge_with_ffmpeg(self, 
                          video_path: str, 
                          srt_path: str, 
                          output_path: str,
                          style: Dict,
                          quality: str) -> Dict[str, Any]:
        try:
            video_codec, bitrate = self._get_quality_settings(quality)
            
            # Build style options for subtitles
            subtitle_style = self._build_subtitle_filter_simple(style)
            
            # Use subprocess for more control over FFmpeg execution
            import subprocess
            
            # Ensure MP4 output format for better macOS compatibility
            if not output_path.lower().endswith('.mp4'):
                base_name = os.path.splitext(output_path)[0]
                output_path = f"{base_name}.mp4"
            
            # Build FFmpeg command manually for better control with macOS compatibility
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{srt_path}':force_style='{subtitle_style}'",
                '-c:v', video_codec,
                '-profile:v', 'baseline',  # Better compatibility with macOS
                '-level', '3.1',  # Widely supported level
                '-pix_fmt', 'yuv420p',  # Ensure compatible pixel format
                '-preset', 'medium',  # Balance between speed and quality
                '-c:a', 'aac',
                '-movflags', '+faststart',  # Optimize for streaming/playback
                '-f', 'mp4',  # Force MP4 container format
                '-y',  # overwrite output file
                output_path
            ]
            
            if bitrate:
                cmd.extend(['-b:v', bitrate])
            
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Run with subprocess for better control
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                error_msg = f"FFmpeg failed with return code {result.returncode}: {result.stderr}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            if not os.path.exists(output_path):
                error_msg = "Output file was not created"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
            
            self.logger.info(f"Successfully merged video with subtitles: {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'file_size': os.path.getsize(output_path)
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "FFmpeg command timed out"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def _build_subtitle_filter_simple(self, style: Dict) -> str:
        """Build a simplified subtitle style string for direct FFmpeg use"""
        parts = []
        
        if 'fontsize' in style:
            parts.append(f"FontSize={style['fontsize']}")
        if 'fontcolor' in style:
            parts.append(f"PrimaryColour=&H{self._color_to_hex(style['fontcolor'])}")
        if 'outline' in style:
            parts.append(f"Outline={style['outline']}")
        if 'outlinecolor' in style:
            parts.append(f"OutlineColour=&H{self._color_to_hex(style['outlinecolor'])}")
        
        return ','.join(parts) if parts else 'FontSize=24,PrimaryColour=&Hffffff,Outline=2,OutlineColour=&H000000'

    def _color_to_hex(self, color: str) -> str:
        """Convert color name to hex for ASS format (BGR format for compatibility)"""
        color_map = {
            'white': 'ffffff',
            'black': '000000',
            'red': 'ff0000',   # Fixed: was BGR, now RGB for better macOS compatibility
            'blue': '0000ff',  # Fixed: was BGR, now RGB for better macOS compatibility
            'green': '00ff00',
            'yellow': 'ffff00'  # Fixed: was BGR, now RGB for better macOS compatibility
        }
        return color_map.get(color.lower(), 'ffffff')

    def _build_subtitle_filter(self, srt_path: str, style: Dict) -> str:
        style_parts = []
        
        for key, value in style.items():
            if key == 'fontsize':
                style_parts.append(f"FontSize={value}")
            elif key == 'fontcolor':
                style_parts.append(f"PrimaryColour={self._color_to_ass(value)}")
            elif key == 'outline':
                style_parts.append(f"Outline={value}")
            elif key == 'outlinecolor':
                style_parts.append(f"OutlineColour={self._color_to_ass(value)}")
            elif key == 'shadow':
                style_parts.append(f"Shadow={value}")
            elif key == 'shadowcolor':
                style_parts.append(f"BackColour={self._color_to_ass(value)}")
            elif key == 'fontname':
                style_parts.append(f"Fontname={value}")
        
        return ','.join(style_parts)

    def _color_to_ass(self, color: str) -> str:
        color_map = {
            'white': '&Hffffff',
            'black': '&H000000',
            'red': '&Hff0000',   # Fixed: was BGR, now RGB for better macOS compatibility
            'blue': '&H0000ff',  # Fixed: was BGR, now RGB for better macOS compatibility
            'green': '&H00ff00',
            'yellow': '&Hffff00'  # Fixed: was BGR, now RGB for better macOS compatibility
        }
        return color_map.get(color.lower(), color)

    def _get_quality_settings(self, quality: str) -> Tuple[str, Optional[str]]:
        """Get video codec and bitrate settings optimized for macOS compatibility"""
        quality_map = {
            'high': ('libx264', '4000k'),      # Reduced from 5000k for better compatibility
            'medium': ('libx264', '2500k'),    # Good balance of quality/compatibility
            'low': ('libx264', '1500k'),       # Increased from 1000k for better quality
            'lossless': ('libx264', None),     # Use CRF for better quality control
            'macos_optimized': ('libx264', '3000k')  # New preset specifically for macOS
        }
        return quality_map.get(quality, ('libx264', '2500k'))

    def batch_process_videos(self, 
                           input_dir: str,
                           output_dir: str,
                           subtitle_lang: str = 'zh-Hans',
                           subtitle_style: Optional[Dict] = None,
                           video_quality: str = 'high') -> List[Dict[str, Any]]:
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        video_files = self._find_video_files(input_path)
        
        self.logger.info(f"Found {len(video_files)} video files to process")
        
        with tqdm(total=len(video_files), desc="Processing videos") as pbar:
            for video_file in video_files:
                pbar.set_description(f"Processing {video_file.name}")
                
                subtitle_file = self._find_matching_subtitle(video_file, subtitle_lang)
                
                if not subtitle_file:
                    result = {
                        'success': False,
                        'error': f'No {subtitle_lang} subtitle found',
                        'video_path': str(video_file)
                    }
                    results.append(result)
                    pbar.update(1)
                    continue
                
                output_file = output_path / f"{video_file.stem}_with_subtitles{video_file.suffix}"
                
                result = self.merge_video_with_subtitles(
                    str(video_file),
                    str(subtitle_file),
                    str(output_file),
                    subtitle_style,
                    video_quality
                )
                
                result['video_name'] = video_file.name
                result['subtitle_lang'] = subtitle_lang
                results.append(result)
                
                pbar.update(1)
        
        success_count = sum(1 for r in results if r.get('success'))
        self.logger.info(f"Batch processing completed: {success_count}/{len(results)} successful")
        
        return results

    def _find_video_files(self, directory: Path) -> List[Path]:
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
        video_files = []
        
        for file_path in directory.rglob('*'):
            if file_path.suffix.lower() in video_extensions and not file_path.name.endswith('.part'):
                video_files.append(file_path)
        
        return sorted(video_files)

    def _find_matching_subtitle(self, video_file: Path, subtitle_lang: str) -> Optional[Path]:
        base_name = video_file.stem
        subtitle_extensions = ['.vtt', '.srt']
        
        for ext in subtitle_extensions:
            subtitle_file = video_file.parent / f"{base_name}.{subtitle_lang}{ext}"
            if subtitle_file.exists():
                return subtitle_file
            
            subtitle_file = video_file.parent / f"{base_name}.{subtitle_lang.split('-')[0]}{ext}"
            if subtitle_file.exists():
                return subtitle_file
        
        return None

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            info = {
                'duration': float(probe['format']['duration']),
                'size': int(probe['format']['size']),
                'bitrate': int(probe['format']['bit_rate']),
            }
            
            if video_stream:
                info.update({
                    'width': int(video_stream['width']),
                    'height': int(video_stream['height']),
                    'fps': eval(video_stream['r_frame_rate']),
                    'video_codec': video_stream['codec_name']
                })
            
            if audio_stream:
                info.update({
                    'audio_codec': audio_stream['codec_name'],
                    'audio_bitrate': int(audio_stream.get('bit_rate', 0))
                })
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get video info: {str(e)}")
            return {}