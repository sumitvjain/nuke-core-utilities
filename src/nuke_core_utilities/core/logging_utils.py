"""
Advanced logging utilities for Nuke pipeline
"""

import logging
import logging.handlers
import os
import sys
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import nuke

from .constants import LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR, LOG_CRITICAL
from .constants import LOG_FORMAT_DETAILED, LOG_FILE_APP, LOG_FILE_ERROR

class NukeLogFormatter(logging.Formatter):
    """Custom formatter for Nuke logs"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        if fmt is None:
            fmt = LOG_FORMAT_DETAILED
        super().__init__(fmt, datefmt, style)
        
    def format(self, record):
        # Add Nuke-specific information
        if hasattr(nuke, 'root'):
            record.nuke_frame = nuke.frame() if hasattr(nuke, 'frame') else 0
            record.nuke_script = nuke.root().name() if nuke.root().name() else 'unsaved'
        else:
            record.nuke_frame = 0
            record.nuke_script = 'unsaved'
        
        # Add custom fields
        record.function_name = record.funcName if hasattr(record, 'funcName') else ''
        record.line_number = record.lineno if hasattr(record, 'lineno') else 0
        
        return super().format(record)

class NukeConsoleHandler(logging.StreamHandler):
    """Handler that outputs to Nuke's Script Editor"""
    
    def __init__(self):
        super().__init__()
        self.setFormatter(NukeLogFormatter())
        
    def emit(self, record):
        try:
            msg = self.format(record)
            
            # Color code messages based on level
            if record.levelno >= logging.ERROR:
                # Error - Red
                nuke.tprint(f"<span style='color:#FF5555'>{msg}</span>")
            elif record.levelno >= logging.WARNING:
                # Warning - Orange
                nuke.tprint(f"<span style='color:#FFAA00'>{msg}</span>")
            elif record.levelno >= logging.INFO:
                # Info - Green
                nuke.tprint(f"<span style='color:#55FF55'>{msg}</span>")
            else:
                # Debug - Gray
                nuke.tprint(f"<span style='color:#AAAAAA'>{msg}</span>")
                
        except Exception:
            self.handleError(record)

class NukeFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler with JSON support"""
    
    def __init__(self, filename, max_bytes=10*1024*1024, backup_count=5):
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)
        self.setFormatter(NukeLogFormatter())
        
    def emit(self, record):
        # Add extra metadata before formatting
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.now().isoformat()
        if not hasattr(record, 'process_id'):
            record.process_id = os.getpid()
        
        super().emit(record)

class JSONLogHandler(logging.Handler):
    """Handler that writes logs in JSON format"""
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': os.getpid(),
            'thread': record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add Nuke-specific info
        try:
            log_entry['nuke'] = {
                'frame': nuke.frame(),
                'script': nuke.root().name(),
                'node': getattr(record, 'node_name', None)
            }
        except:
            log_entry['nuke'] = None
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key.startswith('custom_'):
                log_entry[key] = value
        
        # Write to file
        try:
            with open(self.filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            self.handleError(record)

class NukeLogger:
    """Main logger class for Nuke pipeline"""
    
    _loggers = {}
    
    def __init__(self, name: str = "nuke_core", level: str = LOG_INFO):
        self.name = name
        self.level = getattr(logging, level.upper())
        
        # Get or create logger
        if name in self._loggers:
            self.logger = self._loggers[name]
        else:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(self.level)
            self.logger.propagate = False
            
            # Clear existing handlers
            self.logger.handlers.clear()
            
            # Add handlers
            self._setup_handlers()
            
            self._loggers[name] = self.logger
    
    def _setup_handlers(self):
        """Setup all log handlers"""
        
        # Console handler (Nuke Script Editor)
        console_handler = NukeConsoleHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # File handler
        from .env import get_env
        env = get_env()
        log_dir = env.get_path('project_logs', Path.home() / 'nuke_logs')
        Path(log_dir).mkdir(exist_ok=True)
        
        app_log = Path(log_dir) / LOG_FILE_APP
        file_handler = NukeFileHandler(str(app_log))
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_log = Path(log_dir) / LOG_FILE_ERROR
        error_handler = NukeFileHandler(str(error_log))
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
        # JSON handler for structured logging
        json_log = Path(log_dir) / 'nuke_structured.log'
        json_handler = JSONLogHandler(str(json_log))
        json_handler.setLevel(logging.INFO)
        self.logger.addHandler(json_handler)
    
    def log_node_operation(self, operation: str, node_name: str, 
                          details: Dict = None, level: str = LOG_INFO):
        """Log node operations with context"""
        log_data = {
            'operation': operation,
            'node': node_name,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        log_method = getattr(self.logger, level.lower())
        extra = {'custom_data': log_data, 'node_name': node_name}
        log_method(f"Node {operation}: {node_name}", extra=extra)
    
    def log_render(self, render_info: Dict, level: str = LOG_INFO):
        """Log render operations"""
        log_method = getattr(self.logger, level.lower())
        extra = {'custom_render': render_info}
        log_method(f"Render: {render_info.get('node', 'Unknown')}", extra=extra)
    
    def log_performance(self, operation: str, duration: float, 
                       details: Dict = None, level: str = LOG_INFO):
        """Log performance metrics"""
        log_method = getattr(self.logger, level.lower())
        extra = {
            'custom_performance': {
                'operation': operation,
                'duration': duration,
                'details': details or {}
            }
        }
        log_method(f"Performance: {operation} took {duration:.3f}s", extra=extra)
    
    def log_user_action(self, action: str, user: str = None, 
                       details: Dict = None, level: str = LOG_INFO):
        """Log user actions"""
        from .env import get_env
        env = get_env()
        
        if user is None:
            user = env.get_user_info().get('username', 'unknown')
        
        log_method = getattr(self.logger, level.lower())
        extra = {
            'custom_user_action': {
                'user': user,
                'action': action,
                'details': details or {},
                'timestamp': datetime.now().isoformat()
            }
        }
        log_method(f"User action: {user} - {action}", extra=extra)
    
    def exception(self, msg: str, exc_info: bool = True, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(msg, exc_info=exc_info, extra=kwargs)
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=kwargs)
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=kwargs)
    
    def set_level(self, level: str):
        """Set log level"""
        level_num = getattr(logging, level.upper())
        self.logger.setLevel(level_num)
        for handler in self.logger.handlers:
            handler.setLevel(level_num)
    
    def get_log_file(self) -> Optional[Path]:
        """Get path to main log file"""
        for handler in self.logger.handlers:
            if isinstance(handler, NukeFileHandler):
                return Path(handler.baseFilename)
        return None
    
    def analyze_logs(self, log_file: Path = None, 
                    filters: Dict[str, Any] = None) -> List[Dict]:
        """Analyze log entries"""
        if log_file is None:
            log_file = self.get_log_file()
        
        if not log_file or not log_file.exists():
            return []
        
        logs = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Parse log line (simplified)
                    # In production, you'd use proper log parsing
                    logs.append({'raw': line.strip()})
        except Exception as e:
            self.error(f"Failed to analyze logs: {e}")
        
        return logs

# Global logger instance
_logger = None

def get_logger(name: str = "nuke_core", level: str = LOG_INFO) -> NukeLogger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None or _logger.name != name:
        _logger = NukeLogger(name, level)
    return _logger

def setup_logging(level: str = LOG_INFO, 
                 log_to_console: bool = True,
                 log_to_file: bool = True):
    """Setup global logging configuration"""
    logger = get_logger(level=level)
    
    if not log_to_console:
        # Remove console handlers
        for handler in logger.logger.handlers[:]:
            if isinstance(handler, NukeConsoleHandler):
                logger.logger.removeHandler(handler)
    
    if not log_to_file:
        # Remove file handlers
        for handler in logger.logger.handlers[:]:
            if isinstance(handler, (NukeFileHandler, JSONLogHandler)):
                logger.logger.removeHandler(handler)
    
    return logger

# Context manager for timing operations
class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, logger: NukeLogger = None):
        self.operation_name = operation_name
        self.logger = logger or get_logger()
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log_performance(self.operation_name, duration)
        else:
            self.logger.error(
                f"Operation '{self.operation_name}' failed after {duration:.3f}s",
                exc_info=(exc_type, exc_val, exc_tb)
            )

# Decorator for logging function calls
def log_function_call(logger: NukeLogger = None, level: str = LOG_DEBUG):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            func_name = func.__name__
            
            log.debug(f"Calling {func_name}", extra={
                'custom_function_call': {
                    'function': func_name,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            })
            
            try:
                result = func(*args, **kwargs)
                log.debug(f"{func_name} completed successfully")
                return result
            except Exception as e:
                log.exception(f"{func_name} failed with exception")
                raise
        
        return wrapper
    return decorator

# Initialize default logger on import
default_logger = get_logger()