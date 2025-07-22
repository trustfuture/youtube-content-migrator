import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import configparser


class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path.home() / '.youtube-migrator' / 'config.ini'
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.config = configparser.ConfigParser()
        self.default_config = self._get_default_config()
        self.load_config()

    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        return {
            'download': {
                'output_path': './downloads',
                'quality': 'best',
                'format': 'mp4',
                'audio_only': False,
                'download_subtitles': True,
                'subtitle_languages': 'en,zh,zh-Hans,zh-Hant',
                'download_thumbnails': True,
                'download_metadata': True,
                'concurrent_downloads': 3,
                'rate_limit': None,
                'retry_attempts': 3,
            },
            'organization': {
                'organize_by_channel': True,
                'organize_by_date': False,
                'organize_by_playlist': True,
                'create_subdirectories': True,
                'filename_template': '%%(title)s_%%(id)s.%%(ext)s',
                'sanitize_filenames': True,
                'max_filename_length': 200,
                'cleanup_empty_dirs': True,
            },
            'metadata': {
                'extract_comments': False,
                'extract_full_description': True,
                'extract_chapters': True,
                'export_format': 'json',
                'include_thumbnails_metadata': True,
                'include_technical_info': True,
                'include_engagement_metrics': True,
            },
            'logging': {
                'level': 'INFO',
                'log_file': './logs/youtube-migrator.log',
                'max_log_size_mb': 10,
                'backup_count': 5,
                'console_output': True,
                'detailed_progress': True,
            },
            'advanced': {
                'use_proxy': False,
                'proxy_url': None,
                'custom_headers': None,
                'respect_rate_limits': True,
                'skip_unavailable': True,
                'ignore_errors': False,
                'archive_file': './archive.txt',
                'cookies_file': None,
            },
            'video_processing': {
                'default_subtitle_language': 'zh-Hans',
                'output_quality': 'high',
                'subtitle_fontsize': 24,
                'subtitle_fontcolor': 'white',
                'subtitle_outline': 2,
                'subtitle_outlinecolor': 'black',
                'subtitle_shadow': 1,
                'subtitle_shadowcolor': 'black',
                'subtitle_fontname': 'Arial',
                'temp_directory': None,
                'keep_original_files': True,
                'concurrent_processing': 2,
            }
        }

    def load_config(self):
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
                self.logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                self.logger.error(f"Failed to load config file: {str(e)}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        self.logger.info("Creating default configuration")
        
        for section_name, section_data in self.default_config.items():
            self.config.add_section(section_name)
            for key, value in section_data.items():
                if isinstance(value, (list, dict)):
                    self.config.set(section_name, key, json.dumps(value))
                else:
                    self.config.set(section_name, key, str(value))
        
        self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        try:
            value = self.config.get(section, key)
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                if value.lower() in ('true', 'false'):
                    return value.lower() == 'true'
                elif value.isdigit():
                    return int(value)
                elif value.replace('.', '').isdigit():
                    return float(value)
                elif value.lower() == 'none':
                    return None
                else:
                    return value
                    
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            return self.default_config.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any):
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        if isinstance(value, (list, dict)):
            self.config.set(section, key, json.dumps(value))
        else:
            self.config.set(section, key, str(value))

    def get_download_config(self) -> Dict[str, Any]:
        return {
            'output_path': self.get('download', 'output_path'),
            'quality': self.get('download', 'quality'),
            'format': self.get('download', 'format'),
            'audio_only': self.get('download', 'audio_only'),
            'download_subtitles': self.get('download', 'download_subtitles'),
            'subtitle_languages': self.get('download', 'subtitle_languages'),
            'download_thumbnails': self.get('download', 'download_thumbnails'),
            'download_metadata': self.get('download', 'download_metadata'),
            'concurrent_downloads': self.get('download', 'concurrent_downloads'),
            'rate_limit': self.get('download', 'rate_limit'),
            'retry_attempts': self.get('download', 'retry_attempts'),
        }

    def get_organization_config(self) -> Dict[str, Any]:
        return {
            'organize_by_channel': self.get('organization', 'organize_by_channel'),
            'organize_by_date': self.get('organization', 'organize_by_date'),
            'organize_by_playlist': self.get('organization', 'organize_by_playlist'),
            'create_subdirectories': self.get('organization', 'create_subdirectories'),
            'filename_template': self.get('organization', 'filename_template'),
            'sanitize_filenames': self.get('organization', 'sanitize_filenames'),
            'max_filename_length': self.get('organization', 'max_filename_length'),
            'cleanup_empty_dirs': self.get('organization', 'cleanup_empty_dirs'),
        }

    def get_metadata_config(self) -> Dict[str, Any]:
        return {
            'extract_comments': self.get('metadata', 'extract_comments'),
            'extract_full_description': self.get('metadata', 'extract_full_description'),
            'extract_chapters': self.get('metadata', 'extract_chapters'),
            'export_format': self.get('metadata', 'export_format'),
            'include_thumbnails_metadata': self.get('metadata', 'include_thumbnails_metadata'),
            'include_technical_info': self.get('metadata', 'include_technical_info'),
            'include_engagement_metrics': self.get('metadata', 'include_engagement_metrics'),
        }

    def get_logging_config(self) -> Dict[str, Any]:
        return {
            'level': self.get('logging', 'level'),
            'log_file': self.get('logging', 'log_file'),
            'max_log_size_mb': self.get('logging', 'max_log_size_mb'),
            'backup_count': self.get('logging', 'backup_count'),
            'console_output': self.get('logging', 'console_output'),
            'detailed_progress': self.get('logging', 'detailed_progress'),
        }

    def get_advanced_config(self) -> Dict[str, Any]:
        return {
            'use_proxy': self.get('advanced', 'use_proxy'),
            'proxy_url': self.get('advanced', 'proxy_url'),
            'custom_headers': self.get('advanced', 'custom_headers'),
            'respect_rate_limits': self.get('advanced', 'respect_rate_limits'),
            'skip_unavailable': self.get('advanced', 'skip_unavailable'),
            'ignore_errors': self.get('advanced', 'ignore_errors'),
            'archive_file': self.get('advanced', 'archive_file'),
            'cookies_file': self.get('advanced', 'cookies_file'),
        }

    def get_video_processing_config(self) -> Dict[str, Any]:
        return {
            'default_subtitle_language': self.get('video_processing', 'default_subtitle_language'),
            'output_quality': self.get('video_processing', 'output_quality'),
            'subtitle_fontsize': self.get('video_processing', 'subtitle_fontsize'),
            'subtitle_fontcolor': self.get('video_processing', 'subtitle_fontcolor'),
            'subtitle_outline': self.get('video_processing', 'subtitle_outline'),
            'subtitle_outlinecolor': self.get('video_processing', 'subtitle_outlinecolor'),
            'subtitle_shadow': self.get('video_processing', 'subtitle_shadow'),
            'subtitle_shadowcolor': self.get('video_processing', 'subtitle_shadowcolor'),
            'subtitle_fontname': self.get('video_processing', 'subtitle_fontname'),
            'temp_directory': self.get('video_processing', 'temp_directory'),
            'keep_original_files': self.get('video_processing', 'keep_original_files'),
            'concurrent_processing': self.get('video_processing', 'concurrent_processing'),
        }

    def update_section(self, section: str, config_dict: Dict[str, Any]):
        for key, value in config_dict.items():
            self.set(section, key, value)
        self.save_config()

    def reset_to_defaults(self):
        self.config.clear()
        self._create_default_config()

    def export_config(self, export_path: str) -> bool:
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = {}
            for section in self.config.sections():
                config_dict[section] = dict(self.config.items(section))
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration exported to {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {str(e)}")
            return False

    def import_config(self, import_path: str) -> bool:
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                self.logger.error(f"Import file does not exist: {import_path}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            self.config.clear()
            for section_name, section_data in config_dict.items():
                self.config.add_section(section_name)
                for key, value in section_data.items():
                    self.config.set(section_name, key, str(value))
            
            self.save_config()
            self.logger.info(f"Configuration imported from {import_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {str(e)}")
            return False

    def validate_config(self) -> Dict[str, List[str]]:
        issues = {
            'errors': [],
            'warnings': []
        }
        
        output_path = self.get('download', 'output_path')
        if not os.access(Path(output_path).parent, os.W_OK):
            issues['errors'].append(f"Output path is not writable: {output_path}")
        
        quality = self.get('download', 'quality')
        valid_qualities = ['best', 'worst', '720p', '1080p', 'audio']
        if quality not in valid_qualities:
            issues['warnings'].append(f"Unknown quality setting: {quality}")
        
        concurrent_downloads = self.get('download', 'concurrent_downloads')
        if concurrent_downloads > 10:
            issues['warnings'].append("High concurrent download count may cause rate limiting")
        
        log_file = self.get('logging', 'log_file')
        log_dir = Path(log_file).parent
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                issues['errors'].append(f"Cannot create log directory: {log_dir}")
        
        return issues