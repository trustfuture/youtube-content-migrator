import os
import shutil
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import re
import json


class FileOrganizer:
    def __init__(self, base_output_path: str = "./downloads"):
        self.base_output_path = Path(base_output_path)
        self.logger = logging.getLogger(__name__)
        
        self.base_output_path.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        filename = re.sub(r'[^\w\s\-_\.]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_. ')
        
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename

    def create_channel_structure(self, channel_name: str, channel_id: str) -> Path:
        sanitized_name = self.sanitize_filename(channel_name)
        channel_dir = self.base_output_path / f"{sanitized_name}_{channel_id}"
        
        subdirs = [
            "videos",
            "metadata",
            "thumbnails", 
            "subtitles",
            "playlists"
        ]
        
        for subdir in subdirs:
            (channel_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        return channel_dir

    def create_video_structure(self, video_info: Dict[str, Any], custom_path: Optional[str] = None) -> Dict[str, Path]:
        if custom_path:
            base_path = Path(custom_path)
        else:
            channel_name = video_info.get('uploader', 'Unknown_Channel')
            channel_id = video_info.get('uploader_id', 'unknown_id')
            base_path = self.create_channel_structure(channel_name, channel_id)
        
        video_id = video_info.get('id', 'unknown_id')
        video_title = self.sanitize_filename(video_info.get('title', 'Unknown_Title'))
        
        video_folder = base_path / "videos" / f"{video_title}_{video_id}"
        video_folder.mkdir(parents=True, exist_ok=True)
        
        return {
            'base': base_path,
            'video': video_folder,
            'metadata': base_path / "metadata",
            'thumbnails': base_path / "thumbnails", 
            'subtitles': base_path / "subtitles",
        }

    def organize_downloaded_file(self, file_path: str, video_info: Dict[str, Any], 
                               file_type: str = "video") -> Optional[str]:
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.error(f"Source file does not exist: {file_path}")
                return None
            
            structure = self.create_video_structure(video_info)
            
            video_id = video_info.get('id', 'unknown_id')
            video_title = self.sanitize_filename(video_info.get('title', 'Unknown_Title'))
            
            if file_type == "video":
                target_dir = structure['video']
                filename = f"{video_title}_{video_id}{source_path.suffix}"
            elif file_type == "metadata":
                target_dir = structure['metadata']
                filename = f"{video_title}_{video_id}_metadata.json"
            elif file_type == "thumbnail":
                target_dir = structure['thumbnails']
                filename = f"{video_title}_{video_id}_thumbnail{source_path.suffix}"
            elif file_type == "subtitle":
                target_dir = structure['subtitles']
                lang = video_info.get('subtitle_lang', 'unknown')
                filename = f"{video_title}_{video_id}_{lang}{source_path.suffix}"
            else:
                target_dir = structure['video']
                filename = f"{video_title}_{video_id}_{file_type}{source_path.suffix}"
            
            target_path = target_dir / filename
            target_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(target_path))
            
            self.logger.info(f"Moved {file_path} to {target_path}")
            return str(target_path)
            
        except Exception as e:
            self.logger.error(f"Failed to organize file {file_path}: {str(e)}")
            return None

    def create_playlist_structure(self, playlist_info: Dict[str, Any]) -> Path:
        playlist_title = self.sanitize_filename(playlist_info.get('title', 'Unknown_Playlist'))
        playlist_id = playlist_info.get('id', 'unknown_id')
        uploader = self.sanitize_filename(playlist_info.get('uploader', 'Unknown_Channel'))
        
        playlist_dir = self.base_output_path / uploader / "playlists" / f"{playlist_title}_{playlist_id}"
        playlist_dir.mkdir(parents=True, exist_ok=True)
        
        return playlist_dir

    def organize_playlist_files(self, playlist_info: Dict[str, Any], 
                              video_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            playlist_dir = self.create_playlist_structure(playlist_info)
            
            playlist_manifest = {
                'playlist_info': playlist_info,
                'videos': [],
                'organized_at': datetime.now().isoformat(),
                'total_videos': len(video_files)
            }
            
            for i, video_file in enumerate(video_files, 1):
                video_info = video_file.get('info', {})
                file_path = video_file.get('file_path')
                
                if file_path and Path(file_path).exists():
                    new_path = self.organize_downloaded_file(
                        file_path, video_info, "video"
                    )
                    
                    playlist_manifest['videos'].append({
                        'index': i,
                        'video_id': video_info.get('id'),
                        'title': video_info.get('title'),
                        'original_path': file_path,
                        'organized_path': new_path,
                        'status': 'success' if new_path else 'failed'
                    })
            
            manifest_path = playlist_dir / "playlist_manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_manifest, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'playlist_dir': str(playlist_dir),
                'manifest_path': str(manifest_path),
                'organized_videos': len([v for v in playlist_manifest['videos'] if v['status'] == 'success'])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to organize playlist files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_empty_directories(self, base_path: Optional[str] = None):
        if base_path is None:
            base_path = self.base_output_path
        else:
            base_path = Path(base_path)
        
        try:
            for root, dirs, files in os.walk(base_path, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            self.logger.info(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass
                        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def generate_directory_report(self, target_dir: Optional[str] = None) -> Dict[str, Any]:
        if target_dir is None:
            target_dir = self.base_output_path
        else:
            target_dir = Path(target_dir)
        
        report = {
            'base_directory': str(target_dir),
            'generated_at': datetime.now().isoformat(),
            'channels': [],
            'total_videos': 0,
            'total_size_bytes': 0
        }
        
        try:
            for channel_dir in target_dir.iterdir():
                if channel_dir.is_dir():
                    channel_info = self._analyze_channel_directory(channel_dir)
                    report['channels'].append(channel_info)
                    report['total_videos'] += channel_info['video_count']
                    report['total_size_bytes'] += channel_info['total_size_bytes']
            
            report['total_size_human'] = self._format_size(report['total_size_bytes'])
            
        except Exception as e:
            self.logger.error(f"Failed to generate directory report: {str(e)}")
            report['error'] = str(e)
        
        return report

    def _analyze_channel_directory(self, channel_dir: Path) -> Dict[str, Any]:
        channel_info = {
            'name': channel_dir.name,
            'path': str(channel_dir),
            'video_count': 0,
            'total_size_bytes': 0,
            'subdirectories': []
        }
        
        try:
            for subdir in channel_dir.iterdir():
                if subdir.is_dir():
                    subdir_info = {
                        'name': subdir.name,
                        'file_count': 0,
                        'size_bytes': 0
                    }
                    
                    for file_path in subdir.rglob('*'):
                        if file_path.is_file():
                            subdir_info['file_count'] += 1
                            subdir_info['size_bytes'] += file_path.stat().st_size
                            
                            if subdir.name == 'videos':
                                channel_info['video_count'] += 1
                    
                    subdir_info['size_human'] = self._format_size(subdir_info['size_bytes'])
                    channel_info['subdirectories'].append(subdir_info)
                    channel_info['total_size_bytes'] += subdir_info['size_bytes']
            
            channel_info['total_size_human'] = self._format_size(channel_info['total_size_bytes'])
            
        except Exception as e:
            self.logger.error(f"Failed to analyze channel directory {channel_dir}: {str(e)}")
            channel_info['error'] = str(e)
        
        return channel_info

    def _format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"