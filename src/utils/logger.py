import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import colorama
from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        colorama.init(autoreset=True)
        
        self.colors = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Style.BRIGHT,
        }

    def format(self, record):
        log_color = self.colors.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


def setup_logging(level: str = 'INFO', 
                 log_file: Optional[str] = None,
                 console_output: bool = True,
                 max_log_size_mb: int = 10,
                 backup_count: int = 5):
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    formatters = {
        'detailed': logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ),
        'simple': logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ),
        'colored': ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    }
    
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatters['colored'])
        root_logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_log_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatters['detailed'])
        root_logger.addHandler(file_handler)
    
    yt_dlp_logger = logging.getLogger('yt_dlp')
    yt_dlp_logger.setLevel(logging.WARNING)
    
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.WARNING)


class ProgressLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.current_operation = None
        self.total_items = 0
        self.completed_items = 0

    def start_operation(self, operation_name: str, total_items: int = 0):
        self.current_operation = operation_name
        self.total_items = total_items
        self.completed_items = 0
        
        if total_items > 0:
            self.logger.info(f"Starting {operation_name} - {total_items} items to process")
        else:
            self.logger.info(f"Starting {operation_name}")

    def update_progress(self, message: str = None, increment: int = 1):
        self.completed_items += increment
        
        if self.total_items > 0:
            percentage = (self.completed_items / self.total_items) * 100
            progress_msg = f"Progress: {self.completed_items}/{self.total_items} ({percentage:.1f}%)"
            
            if message:
                progress_msg += f" - {message}"
                
            self.logger.info(progress_msg)
        elif message:
            self.logger.info(f"{self.current_operation}: {message}")

    def finish_operation(self, success_count: int = None, error_count: int = None):
        if success_count is not None and error_count is not None:
            total = success_count + error_count
            self.logger.info(
                f"Completed {self.current_operation} - "
                f"Success: {success_count}/{total}, Errors: {error_count}/{total}"
            )
        else:
            self.logger.info(f"Completed {self.current_operation}")
        
        self.current_operation = None
        self.total_items = 0
        self.completed_items = 0


class ErrorTracker:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.errors = []
        self.warnings = []

    def add_error(self, error_msg: str, exception: Optional[Exception] = None):
        self.errors.append({
            'message': error_msg,
            'exception': str(exception) if exception else None
        })
        
        if exception:
            self.logger.error(f"{error_msg}: {str(exception)}")
        else:
            self.logger.error(error_msg)

    def add_warning(self, warning_msg: str):
        self.warnings.append(warning_msg)
        self.logger.warning(warning_msg)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def get_error_count(self) -> int:
        return len(self.errors)

    def get_warning_count(self) -> int:
        return len(self.warnings)

    def get_summary(self) -> str:
        if not self.has_errors() and not self.has_warnings():
            return "No errors or warnings"
        
        summary = []
        if self.has_errors():
            summary.append(f"{self.get_error_count()} error(s)")
        if self.has_warnings():
            summary.append(f"{self.get_warning_count()} warning(s)")
        
        return ", ".join(summary)

    def print_summary(self):
        if self.has_errors():
            print(f"\n{Fore.RED}Errors ({self.get_error_count()}):") 
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error['message']}")
                if error['exception']:
                    print(f"     Exception: {error['exception']}")
        
        if self.has_warnings():
            print(f"\n{Fore.YELLOW}Warnings ({self.get_warning_count()}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

    def clear(self):
        self.errors.clear()
        self.warnings.clear()