import argparse
import sys
import logging
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from .config.settings import ConfigManager
from .downloader.youtube_downloader import YouTubeDownloader
from .downloader.listing import list_entries
from .metadata.extractor import MetadataExtractor
from .organizer.file_organizer import FileOrganizer
from .processor.video_processor import VideoProcessor
from .utils.logger import setup_logging
from .utils.manifest import write_manifest
from .utils.state import find_existing_video_dir


class YouTubeMigratorCLI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.setup_logging()

        self.downloader = None
        self.metadata_extractor = MetadataExtractor()
        self.file_organizer = None
        self.video_processor = VideoProcessor()

    def setup_logging(self):
        logging_config = self.config_manager.get_logging_config()
        setup_logging(
            level=logging_config['level'],
            log_file=logging_config['log_file'],
            console_output=logging_config['console_output']
        )
        self.logger = logging.getLogger(__name__)

    def create_parser(self):
        parser = argparse.ArgumentParser(
            description='YouTube Content Migrator - Download and organize YouTube videos with metadata',
            prog='youtube-migrator'
        )

        parser.add_argument('--version', action='version', version='1.0.0')

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        self._add_download_parser(subparsers)
        self._add_metadata_parser(subparsers)
        self._add_config_parser(subparsers)
        self._add_organize_parser(subparsers)
        self._add_report_parser(subparsers)
        self._add_merge_parser(subparsers)

        return parser

    def _add_download_parser(self, subparsers):
        download_parser = subparsers.add_parser('download', help='Download YouTube videos')
        download_parser.add_argument('urls', nargs='+', help='YouTube URLs to download')
        download_parser.add_argument('-o', '--output', help='Output directory')
        download_parser.add_argument('-q', '--quality',
                                   choices=['best', 'worst', '720p', '1080p', 'audio'],
                                   help='Video quality')
        download_parser.add_argument('--audio-only', action='store_true',
                                   help='Download audio only')
        download_parser.add_argument('--no-metadata', action='store_true',
                                   help='Skip metadata extraction')
        download_parser.add_argument('--no-organize', action='store_true',
                                   help='Skip file organization')
        download_parser.add_argument('--playlist', action='store_true',
                                   help='Treat URLs as playlists')
        download_parser.add_argument('--channel', action='store_true',
                                   help='Treat URLs as channels')
        download_parser.add_argument('--limit', type=int,
                                   help='Limit number of videos to download')
        download_parser.add_argument('--dry-run', action='store_true',
                                   help='List what would be downloaded without downloading')
        download_parser.add_argument('--force', action='store_true',
                                   help='Redownload even if the video appears to be already downloaded')

    def _add_metadata_parser(self, subparsers):
        metadata_parser = subparsers.add_parser('metadata', help='Extract metadata only')
        metadata_parser.add_argument('urls', nargs='+', help='YouTube URLs')
        metadata_parser.add_argument('-o', '--output', help='Output directory for metadata')
        metadata_parser.add_argument('--format', choices=['json', 'csv'],
                                   default='json', help='Output format')

    def _add_config_parser(self, subparsers):
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_subparsers = config_parser.add_subparsers(dest='config_action')

        config_subparsers.add_parser('show', help='Show current configuration')
        config_subparsers.add_parser('reset', help='Reset to default configuration')

        config_subparsers.add_parser('validate', help='Validate configuration')

        export_parser = config_subparsers.add_parser('export', help='Export configuration')
        export_parser.add_argument('file', help='Export file path')

        import_parser = config_subparsers.add_parser('import', help='Import configuration')
        import_parser.add_argument('file', help='Import file path')

        set_parser = config_subparsers.add_parser('set', help='Set configuration value')
        set_parser.add_argument('section', help='Configuration section')
        set_parser.add_argument('key', help='Configuration key')
        set_parser.add_argument('value', help='Configuration value')

    def _add_organize_parser(self, subparsers):
        organize_parser = subparsers.add_parser('organize', help='Organize existing files')
        organize_parser.add_argument('path', help='Path to organize')
        organize_parser.add_argument('-o', '--output', help='Output directory')
        organize_parser.add_argument('--cleanup', action='store_true',
                                   help='Clean up empty directories')

    def _add_report_parser(self, subparsers):
        report_parser = subparsers.add_parser('report', help='Generate reports')
        report_parser.add_argument('path', help='Path to analyze')
        report_parser.add_argument('-o', '--output', help='Output file for report')
        report_parser.add_argument('--format', choices=['json', 'text'],
                                 default='text', help='Report format')

    def _add_merge_parser(self, subparsers):
        merge_parser = subparsers.add_parser('merge', help='Merge videos with subtitles')
        merge_parser.add_argument('input', help='Input directory or video file')
        merge_parser.add_argument('-o', '--output', help='Output directory')
        merge_parser.add_argument('-l', '--lang', default='zh-Hans',
                                choices=['zh-Hans', 'zh-Hant', 'zh', 'en'],
                                help='Subtitle language (default: zh-Hans)')
        merge_parser.add_argument('-q', '--quality', default='high',
                                choices=['high', 'medium', 'low', 'lossless'],
                                help='Output video quality (default: high)')
        merge_parser.add_argument('--fontsize', type=int, default=24,
                                help='Subtitle font size (default: 24)')
        merge_parser.add_argument('--fontcolor', default='white',
                                help='Subtitle font color (default: white)')
        merge_parser.add_argument('--outline', type=int, default=2,
                                help='Subtitle outline thickness (default: 2)')
        merge_parser.add_argument('--batch', action='store_true',
                                help='Process all videos in directory')
        merge_parser.add_argument('--dry-run', action='store_true',
                                help='Show what would be processed without actually doing it')

    def handle_download(self, args):
        download_config = self.config_manager.get_download_config()

        output_path = args.output or download_config['output_path']
        quality = args.quality or download_config['quality']

        if args.audio_only:
            quality = 'audio'

        self.downloader = YouTubeDownloader(output_path, quality)
        self.file_organizer = FileOrganizer(output_path)

        results = []

        for url in args.urls:
            self.logger.info(f"Processing URL: {url}")

            # For playlist/channel dry-run, list entries and continue.
            if args.dry_run and (args.playlist or args.channel):
                entries = list_entries(url, limit=args.limit)
                results.append(
                    {
                        'success': True,
                        'url': url,
                        'dry_run': True,
                        'entries': entries,
                        'count': len(entries),
                    }
                )
                continue

            try:
                if args.playlist:
                    result = self.downloader.download_playlist(url)
                elif args.channel:
                    result = self.downloader.download_channel(url, args.limit)
                else:
                    # Single video flow: organize into canonical folder, dedupe, and optionally dry-run.
                    info = self.downloader.get_video_info(url)
                    if not info:
                        raise Exception("Failed to extract video information")

                    video_id = info.get('id')
                    if video_id and not args.force:
                        existing = find_existing_video_dir(output_path, video_id)
                        if existing:
                            results.append(
                                {
                                    'success': True,
                                    'url': url,
                                    'skipped': True,
                                    'reason': 'already-downloaded',
                                    'video_id': video_id,
                                    'video_dir': str(existing),
                                    'info': info,
                                }
                            )
                            continue

                    structure = self.file_organizer.create_video_structure(info)
                    base_dir = structure['video']

                    if args.dry_run:
                        results.append(
                            {
                                'success': True,
                                'url': url,
                                'dry_run': True,
                                'video_id': video_id,
                                'video_dir': str(base_dir),
                                'info': info,
                            }
                        )
                        continue

                    custom_opts = {
                        'outtmpl': str(base_dir / '%(title)s_%(id)s.%(ext)s')
                    }
                    result = self.downloader.download_video(url, custom_opts=custom_opts)
                    result['video_dir'] = str(base_dir)

                if not args.no_metadata and isinstance(result, dict) and result.get('success'):
                    metadata = self.metadata_extractor.extract_video_metadata(url)
                    if metadata:
                        self.metadata_extractor.save_metadata(
                            metadata,
                            str(Path(output_path) / 'metadata'),
                        )
                        result['extracted_metadata'] = metadata

                results.append(result)

            except Exception as e:
                self.logger.error(f"Failed to process {url}: {str(e)}")
                results.append({'success': False, 'error': str(e), 'url': url})

        # Write per-video manifests when possible (single-video downloads only).
        for r in results:
            try:
                if isinstance(r, dict) and r.get('success') and r.get('video_dir') and r.get('info'):
                    video_dir = Path(r['video_dir'])
                    if r.get('dry_run') or r.get('skipped'):
                        # Still useful to have a manifest stub for planned/skipped entries.
                        pass
                    manifest = {
                        'generated_at': datetime.now().isoformat(),
                        'url': r.get('info', {}).get('webpage_url') or r.get('url'),
                        'video_id': r.get('info', {}).get('id') or r.get('video_id'),
                        'title': r.get('info', {}).get('title'),
                        'uploader': r.get('info', {}).get('uploader'),
                        'status': 'skipped' if r.get('skipped') else ('dry-run' if r.get('dry_run') else 'downloaded'),
                        'paths': {
                            'video_dir': str(video_dir),
                            'prepared_filename': r.get('prepared_filename'),
                        },
                    }
                    write_manifest(video_dir / 'manifest.json', manifest)
            except Exception:
                pass

        # Write a session report for debugging/auditing.
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'command': 'download',
                'output_path': output_path,
                'results': results,
            }
            write_manifest(Path(output_path) / 'report.json', report)
        except Exception:
            pass

        self._print_download_results(results)

    def handle_metadata(self, args):
        output_path = args.output or './metadata'

        results = self.metadata_extractor.batch_extract_metadata(args.urls, output_path)

        # Persist in requested format as a convenience (batch_extract defaults to json).
        if args.format == 'csv':
            for r in results:
                if r.get('success') and r.get('metadata'):
                    self.metadata_extractor.save_metadata(r['metadata'], output_path, fmt='csv')

        self._print_metadata_results(results)

    def handle_config(self, args):
        if args.config_action == 'show':
            self._show_config()
        elif args.config_action == 'reset':
            self.config_manager.reset_to_defaults()
            print("Configuration reset to defaults")
        elif args.config_action == 'validate':
            issues = self.config_manager.validate_config()
            self._print_validation_results(issues)
        elif args.config_action == 'export':
            if self.config_manager.export_config(args.file):
                print(f"Configuration exported to {args.file}")
            else:
                print("Failed to export configuration", file=sys.stderr)
        elif args.config_action == 'import':
            if self.config_manager.import_config(args.file):
                print(f"Configuration imported from {args.file}")
            else:
                print("Failed to import configuration", file=sys.stderr)
        elif args.config_action == 'set':
            self.config_manager.set(args.section, args.key, args.value)
            self.config_manager.save_config()
            print(f"Set {args.section}.{args.key} = {args.value}")

    def handle_organize(self, args):
        output_path = args.output or args.path
        self.file_organizer = FileOrganizer(output_path)

        if args.cleanup:
            self.file_organizer.cleanup_empty_directories(args.path)
            print("Cleaned up empty directories")

    def handle_report(self, args):
        self.file_organizer = FileOrganizer()
        report = self.file_organizer.generate_directory_report(args.path)

        if args.format == 'json':
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Report saved to {args.output}")
            else:
                import json
                print(json.dumps(report, indent=2))
        else:
            self._print_text_report(report)

    def handle_merge(self, args):
        input_path = Path(args.input)

        if not input_path.exists():
            print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
            return

        output_dir = args.output or str(input_path.parent / "merged_videos")

        subtitle_style = {
            'fontsize': args.fontsize,
            'fontcolor': args.fontcolor,
            'outline': args.outline,
            'outlinecolor': 'black',
            'shadow': 1,
            'shadowcolor': 'black'
        }

        if input_path.is_file():
            self._handle_single_video_merge(input_path, output_dir, args, subtitle_style)
        elif input_path.is_dir() and args.batch:
            self._handle_batch_video_merge(input_path, output_dir, args, subtitle_style)
        else:
            print("Error: For directory input, use --batch flag", file=sys.stderr)
            return

    def _handle_single_video_merge(self, video_path, output_dir, args, subtitle_style):
        subtitle_file = self._find_subtitle_for_video(video_path, args.lang)

        if not subtitle_file:
            print(f"Error: No {args.lang} subtitle found for {video_path.name}", file=sys.stderr)
            return

        output_file = Path(output_dir) / f"{video_path.stem}_with_subtitles{video_path.suffix}"

        if args.dry_run:
            print("Would merge:")
            print(f"  Video: {video_path}")
            print(f"  Subtitle: {subtitle_file}")
            print(f"  Output: {output_file}")
            print(f"  Language: {args.lang}")
            print(f"  Quality: {args.quality}")
            return

        print(f"Merging {video_path.name} with {args.lang} subtitles...")

        result = self.video_processor.merge_video_with_subtitles(
            str(video_path),
            str(subtitle_file),
            str(output_file),
            subtitle_style,
            args.quality
        )

        if result.get('success'):
            file_size = result.get('file_size', 0) / (1024 * 1024)
            print(f"✓ Successfully created: {output_file} ({file_size:.1f} MB)")
        else:
            print(f"✗ Failed to merge: {result.get('error', 'Unknown error')}", file=sys.stderr)

    def _handle_batch_video_merge(self, input_dir, output_dir, args, subtitle_style):
        if args.dry_run:
            video_files = self.video_processor._find_video_files(input_dir)
            print(f"Would process {len(video_files)} video files:")
            for video_file in video_files:
                subtitle_file = self.video_processor._find_matching_subtitle(video_file, args.lang)
                status = "✓" if subtitle_file else "✗ (no subtitle)"
                print(f"  {status} {video_file.name}")
            return

        print(f"Starting batch processing with {args.lang} subtitles...")

        results = self.video_processor.batch_process_videos(
            str(input_dir),
            output_dir,
            args.lang,
            subtitle_style,
            args.quality
        )

        self._print_merge_results(results)

    def _find_subtitle_for_video(self, video_path, lang):
        return self.video_processor._find_matching_subtitle(video_path, lang)

    def _print_merge_results(self, results):
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)

        print(f"\nMerge Results: {successful}/{total} successful")

        for result in results:
            if result.get('success'):
                size_mb = result.get('file_size', 0) / (1024 * 1024)
                print(f"✓ {result.get('video_name')} ({result.get('subtitle_lang')}) - {size_mb:.1f} MB")
            else:
                print(f"✗ {result.get('video_name', 'Unknown')} - {result.get('error', 'Unknown error')}")

        if successful > 0:
            print("\nMerged videos saved to the output directory.")

    def _show_config(self):
        sections = {
            'Download': self.config_manager.get_download_config(),
            'Organization': self.config_manager.get_organization_config(),
            'Metadata': self.config_manager.get_metadata_config(),
            'Logging': self.config_manager.get_logging_config(),
            'Advanced': self.config_manager.get_advanced_config(),
            'Video Processing': self.config_manager.get_video_processing_config(),
        }

        for section_name, config in sections.items():
            print(f"\n[{section_name}]")
            for key, value in config.items():
                print(f"  {key} = {value}")

    def _print_download_results(self, results: List[dict]):
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)

        print(f"\nDownload Results: {successful}/{total} successful")

        for result in results:
            if result.get('success'):
                info = result.get('info', {})
                print(f"✓ {info.get('title', 'Unknown')} - {result.get('url', '')}")
            else:
                print(f"✗ {result.get('url', 'Unknown')} - {result.get('error', 'Unknown error')}")

    def _print_metadata_results(self, results: List[dict]):
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)

        print(f"\nMetadata Extraction Results: {successful}/{total} successful")

        for result in results:
            if result.get('success'):
                print(f"✓ {result.get('url')} - Saved to {result.get('metadata_path')}")
            else:
                print(f"✗ {result.get('url')} - {result.get('error')}")

    def _print_validation_results(self, issues: dict):
        if issues['errors']:
            print("Configuration Errors:")
            for error in issues['errors']:
                print(f"  ✗ {error}")

        if issues['warnings']:
            print("\nConfiguration Warnings:")
            for warning in issues['warnings']:
                print(f"  ⚠ {warning}")

        if not issues['errors'] and not issues['warnings']:
            print("Configuration is valid ✓")

    def _print_text_report(self, report: dict):
        print(f"\nDirectory Report: {report['base_directory']}")
        print(f"Generated: {report['generated_at']}")
        print(f"Total Videos: {report['total_videos']}")
        print(f"Total Size: {report.get('total_size_human', 'Unknown')}")

        print("\nChannels:")
        for channel in report['channels']:
            print(f"  📁 {channel['name']}")
            print(f"     Videos: {channel['video_count']}")
            print(f"     Size: {channel.get('total_size_human', 'Unknown')}")

    def run(self, args: Optional[List[str]] = None):
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return

        try:
            if parsed_args.command == 'download':
                self.handle_download(parsed_args)
            elif parsed_args.command == 'metadata':
                self.handle_metadata(parsed_args)
            elif parsed_args.command == 'config':
                self.handle_config(parsed_args)
            elif parsed_args.command == 'organize':
                self.handle_organize(parsed_args)
            elif parsed_args.command == 'report':
                self.handle_report(parsed_args)
            elif parsed_args.command == 'merge':
                self.handle_merge(parsed_args)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)