import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import yt_dlp
from tqdm import tqdm


class YouTubeDownloader:
    def __init__(self, output_path: str = "./downloads", quality: str = "best"):
        self.output_path = Path(output_path)
        self.quality = quality
        self.logger = logging.getLogger(__name__)
        self.progress_hooks = []
        
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        self.ydl_opts = {
            'format': self._get_format_selector(quality),
            'outtmpl': str(self.output_path / '%(uploader)s/%(title)s.%(ext)s'),
            'writeinfojson': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'zh', 'zh-Hans', 'zh-Hant'],
            'ignoreerrors': True,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
        }

    def _get_format_selector(self, quality: str) -> str:
        format_map = {
            'best': 'best[ext=mp4]/best',
            'worst': 'worst[ext=mp4]/worst',
            '720p': 'best[height<=720][ext=mp4]/best[height<=720]',
            '1080p': 'best[height<=1080][ext=mp4]/best[height<=1080]',
            'audio': 'bestaudio[ext=m4a]/bestaudio/best[ext=m4a]/best',
        }
        return format_map.get(quality, 'best[ext=mp4]/best')

    def _progress_hook(self, d: Dict[str, Any]):
        if d['status'] == 'downloading':
            if hasattr(self, '_current_pbar'):
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    self._current_pbar.update(downloaded - self._current_pbar.n)
        elif d['status'] == 'finished':
            if hasattr(self, '_current_pbar'):
                self._current_pbar.close()
                delattr(self, '_current_pbar')
            self.logger.info(f"Download completed: {d['filename']}")

    def download_video(self, url: str, custom_opts: Optional[Dict] = None) -> Dict[str, Any]:
        opts = self.ydl_opts.copy()
        if custom_opts:
            opts.update(custom_opts)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    raise Exception("Failed to extract video information")

                total_bytes = info.get('filesize') or info.get('filesize_approx', 0)
                if total_bytes:
                    self._current_pbar = tqdm(
                        total=total_bytes,
                        unit='B',
                        unit_scale=True,
                        desc=f"Downloading {info.get('title', 'Unknown')[:30]}..."
                    )

                # Resolve the target filename ahead of time for manifesting.
                prepared = None
                try:
                    prepared = ydl.prepare_filename(info)
                except Exception:
                    prepared = None

                ydl.download([url])

                return {
                    'success': True,
                    'info': info,
                    'output_path': self.output_path,
                    'prepared_filename': prepared,
                }

        except Exception as e:
            self.logger.error(f"Download failed for {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def download_playlist(self, playlist_url: str, custom_opts: Optional[Dict] = None) -> List[Dict[str, Any]]:
        opts = self.ydl_opts.copy()
        opts['extract_flat'] = False
        if custom_opts:
            opts.update(custom_opts)

        results = []
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                
                if not playlist_info or 'entries' not in playlist_info:
                    raise Exception("Failed to extract playlist information")
                
                entries = [entry for entry in playlist_info['entries'] if entry]
                self.logger.info(f"Found {len(entries)} videos in playlist")
                
                for i, entry in enumerate(entries, 1):
                    self.logger.info(f"Downloading video {i}/{len(entries)}: {entry.get('title', 'Unknown')}")
                    
                    try:
                        result = self.download_video(entry['webpage_url'], custom_opts)
                        result['playlist_index'] = i
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Failed to download video {i}: {str(e)}")
                        results.append({
                            'success': False,
                            'error': str(e),
                            'playlist_index': i,
                            'url': entry.get('webpage_url', 'Unknown')
                        })
                
        except Exception as e:
            self.logger.error(f"Playlist download failed: {str(e)}")
            return [{
                'success': False,
                'error': str(e),
                'url': playlist_url
            }]
        
        return results

    def download_channel(self, channel_url: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        opts = self.ydl_opts.copy()
        if limit:
            opts['playlistend'] = limit
            
        return self.download_playlist(channel_url, opts)

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            self.logger.error(f"Failed to get video info for {url}: {str(e)}")
            return None

    def set_output_template(self, template: str):
        self.ydl_opts['outtmpl'] = template

    def set_quality(self, quality: str):
        self.quality = quality
        self.ydl_opts['format'] = self._get_format_selector(quality)