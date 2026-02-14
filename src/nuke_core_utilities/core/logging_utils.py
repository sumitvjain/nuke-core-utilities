"""
Advanced logging utilities for Nuke pipeline

This module provides a comprehensive logging system for Nuke with:
- Custom formatters for Nuke-specific information
- Multiple output handlers (console, file, JSON)
- Structured logging capabilities
- Performance tracking
- User action logging
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
    """
    Custom formatter for Nuke logs that includes Nuke-specific context
    
    Attributes:
        fmt (str): Format string for log messages
        datefmt (str): Format string for dates
        style (str): Style of format string
    """
    
    def __init__(self, fmt: Optional[str] = None, 
                 datefmt: Optional[str] = None, 
                 style: str = '%'):
        """
        Initialize the formatter
        
        Args:
            fmt: Format string (defaults to LOG_FORMAT_DETAILED)
            datefmt: Date format string
            style: Format style ('%' or '{' or '$')
        """
        if fmt is None:
            fmt = LOG_FORMAT_DETAILED
        super().__init__(fmt, datefmt, style)
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the specified log record, adding Nuke-specific information
        
        Args:
            record: LogRecord to format
            
        Returns:
            str: Formatted log message
        """
        # Add Nuke-specific information
        if hasattr(nuke, 'root'):
            record.nuke_frame = nuke.frame() if hasattr(nuke, 'frame') else 0
            record.nuke_script = nuke.root().name() if nuke.root().name() else 'unsaved'
        else:
            record.nuke_frame = 0
            record.nuke_script = 'unsaved'
        
        # Add custom fields for better traceability
        record.function_name = record.funcName if hasattr(record, 'funcName') else ''
        record.line_number = record.lineno if hasattr(record, 'lineno') else 0
        
        return super().format(record)


class NukeConsoleHandler(logging.StreamHandler):
    """
    Handler that outputs colored log messages to Nuke's Script Editor
    
    Colors:
        ERROR: Red (#FF5555)
        WARNING: Orange (#FFAA00)
        INFO: Green (#55FF55)
        DEBUG: Gray (#AAAAAA)
    """
    
    def __init__(self):
        """Initialize handler with custom formatter"""
        super().__init__()
        self.setFormatter(NukeLogFormatter())
        
    def emit(self, record: logging.LogRecord):
        """
        Emit a record to Nuke's Script Editor with color coding
        
        Args:
            record: LogRecord to emit
        """
        try:
            msg = self.format(record)
            
            # Color code messages based on log level
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
    """
    Rotating file handler with automatic log rotation and JSON support
    
    Features:
        - Automatic directory creation
        - Log rotation based on file size
        - Metadata injection
    """
    
    def __init__(self, filename: Union[str, Path], 
                 max_bytes: int = 10*1024*1024,  # 10 MB
                 backup_count: int = 5):
        """
        Initialize rotating file handler
        
        Args:
            filename: Path to log file
            max_bytes: Maximum file size before rotation (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        # Create directory if it doesn't exist
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)
        self.setFormatter(NukeLogFormatter())
        
    def emit(self, record: logging.LogRecord):
        """
        Emit a record, adding metadata before formatting
        
        Args:
            record: LogRecord to emit
        """
        # Add extra metadata for file logging
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.now().isoformat()
        if not hasattr(record, 'process_id'):
            record.process_id = os.getpid()
        
        super().emit(record)


class JSONLogHandler(logging.Handler):
    """
    Handler that writes logs in structured JSON format for easy parsing
    
    Output includes:
        - Standard log fields
        - Exception information
        - Nuke context
        - Custom metadata
    """
    
    def __init__(self, filename: Union[str, Path]):
        """
        Initialize JSON log handler
        
        Args:
            filename: Path to JSON log file
        """
        super().__init__()
        self.filename = filename
        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
    def emit(self, record: logging.LogRecord):
        """
        Emit a record in JSON format
        
        Args:
            record: LogRecord to emit as JSON
        """
        # Create structured log entry
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
        
        # Add Nuke-specific context
        try:
            log_entry['nuke'] = {
                'frame': nuke.frame(),
                'script': nuke.root().name(),
                'node': getattr(record, 'node_name', None)
            }
        except Exception:
            log_entry['nuke'] = None
        
        # Include any custom fields added to the record
        for key, value in record.__dict__.items():
            if key.startswith('custom_'):
                log_entry[key] = value
        
        # Append JSON object to file (one per line)
        try:
            with open(self.filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            self.handleError(record)

def get_loggeVersionManagerr():
    pass
    

    

class NukeLogger:
    """
    Main logger class for Nuke pipeline with multiple logging capabilities
    
    Features:
        - Singleton pattern for logger instances
        - Multiple handlers (console, file, JSON)
        - Specialized logging methods
        - Performance tracking
        - Log analysis
    """
    
    # Class variable to store logger instances (singleton pattern)
    _loggers = {}
    
    def __init__(self, name: str = "nuke_core", level: str = LOG_INFO):
        """
        Initialize Nuke logger
        
        Args:
            name: Logger name (used for singleton retrieval)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        
        # Get or create logger instance
        if name in self._loggers:
            self.logger = self._loggers[name]
        else:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(self.level)
            self.logger.propagate = False  # Prevent duplicate logging
            
            # Clear any existing handlers
            self.logger.handlers.clear()
            
            # Setup all handlers
            self._setup_handlers()
            
            # Store in singleton cache
            self._loggers[name] = self.logger
    
    def _setup_handlers(self):
        """
        Configure all log handlers:
        1. Console handler (Nuke Script Editor)
        2. File handler (rotating logs)
        3. Error file handler (errors only)
        4. JSON handler (structured logging)
        """
        # Console handler (Nuke Script Editor)
        console_handler = NukeConsoleHandler()
        console_handler.setLevel(logging.INFO)  # Don't spam console with DEBUG
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        from .env import get_env
        env = get_env()
        log_dir = env.get_path('project_logs', Path.home() / 'nuke_logs')
        Path(log_dir).mkdir(exist_ok=True)
        
        # Main application log
        app_log = Path(log_dir) / LOG_FILE_APP
        file_handler = NukeFileHandler(str(app_log))
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        self.logger.addHandler(file_handler)
        
        # Separate error log
        error_log = Path(log_dir) / LOG_FILE_ERROR
        error_handler = NukeFileHandler(str(error_log))
        error_handler.setLevel(logging.ERROR)  # Errors only
        self.logger.addHandler(error_handler)
        
        # JSON handler for structured logging and analysis
        json_log = Path(log_dir) / 'nuke_structured.log'
        json_handler = JSONLogHandler(str(json_log))
        json_handler.setLevel(logging.INFO)
        self.logger.addHandler(json_handler)
    
    def log_node_operation(self, operation: str, node_name: str, 
                          details: Optional[Dict] = None, 
                          level: str = LOG_INFO):
        """
        Log node operations with contextual information
        
        Args:
            operation: Type of operation (e.g., 'create', 'delete', 'modify')
            node_name: Name of the node
            details: Additional operation details
            level: Logging level
        """
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
        """
        Log render operations
        
        Args:
            render_info: Dictionary containing render information
            level: Logging level
        """
        log_method = getattr(self.logger, level.lower())
        extra = {'custom_render': render_info}
        log_method(f"Render: {render_info.get('node', 'Unknown')}", extra=extra)
    
    def log_performance(self, operation: str, duration: float, 
                       details: Optional[Dict] = None, 
                       level: str = LOG_INFO):
        """
        Log performance metrics for operations
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            details: Additional performance details
            level: Logging level
        """
        log_method = getattr(self.logger, level.lower())
        extra = {
            'custom_performance': {
                'operation': operation,
                'duration': duration,
                'details': details or {}
            }
        }
        log_method(f"Performance: {operation} took {duration:.3f}s", extra=extra)
    
    def log_user_action(self, action: str, user: Optional[str] = None, 
                       details: Optional[Dict] = None, 
                       level: str = LOG_INFO):
        """
        Log user actions for audit trail
        
        Args:
            action: Description of user action
            user: Username (auto-detected if None)
            details: Additional action details
            level: Logging level
        """
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
        """
        Log exception with traceback
        
        Args:
            msg: Error message
            exc_info: Include exception info if True
            **kwargs: Additional keyword arguments for extra context
        """
        self.logger.exception(msg, exc_info=exc_info, extra=kwargs)
    
    # Convenience methods that mirror standard logging interface
    def critical(self, msg: str, **kwargs):
        """Log CRITICAL level message"""
        self.logger.critical(msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log ERROR level message"""
        self.logger.error(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log WARNING level message"""
        self.logger.warning(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log INFO level message"""
        self.logger.info(msg, extra=kwargs)
    
    def debug(self, msg: str, **kwargs):
        """Log DEBUG level message"""
        self.logger.debug(msg, extra=kwargs)
    
    def set_level(self, level: str):
        """
        Set log level for logger and all handlers
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_num = getattr(logging, level.upper())
        self.logger.setLevel(level_num)
        # Update all handlers
        for handler in self.logger.handlers:
            handler.setLevel(level_num)
    
    def get_log_file(self) -> Optional[Path]:
        """
        Get path to main log file
        
        Returns:
            Path to main log file or None if not found
        """
        for handler in self.logger.handlers:
            if isinstance(handler, NukeFileHandler):
                return Path(handler.baseFilename)
        return None
    
    def analyze_logs(self, log_file: Optional[Path] = None, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Analyze log entries (basic implementation)
        
        Args:
            log_file: Path to log file (uses main log if None)
            filters: Dictionary of filter criteria
            
        Returns:
            List of parsed log entries
        """
        if log_file is None:
            log_file = self.get_log_file()
        
        if not log_file or not log_file.exists():
            return []
        
        logs = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Basic line parsing - extend this for production use
                    logs.append({'raw': line.strip()})
        except Exception as e:
            self.error(f"Failed to analyze logs: {e}")
        
        return logs


# Global logger instance (singleton)
_logger = None

def get_logger(name: str = "nuke_core", level: str = LOG_INFO) -> NukeLogger:
    """
    Get or create global logger instance (singleton pattern)
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        NukeLogger instance
    """
    global _logger
    if _logger is None or _logger.name != name:
        _logger = NukeLogger(name, level)
    return _logger

def setup_logging(level: str = LOG_INFO, 
                 log_to_console: bool = True,
                 log_to_file: bool = True) -> NukeLogger:
    """
    Setup global logging configuration
    
    Args:
        level: Logging level
        log_to_console: Enable console/Script Editor logging
        log_to_file: Enable file logging
        
    Returns:
        Configured NukeLogger instance
    """
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


class TimerContext:
    """
    Context manager for timing operations and logging performance
    
    Usage:
        with TimerContext("operation_name", logger) as timer:
            # Your code here
    """
    
    def __init__(self, operation_name: str, logger: Optional[NukeLogger] = None):
        """
        Initialize timer context
        
        Args:
            operation_name: Name of operation being timed
            logger: Logger instance (uses default if None)
        """
        self.operation_name = operation_name
        self.logger = logger or get_logger()
        self.start_time = None
        
    def __enter__(self) -> 'TimerContext':
        """Start timing when entering context"""
        self.start_time = datetime.now()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop timing and log results when exiting context
        
        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            # Operation succeeded - log performance
            self.logger.log_performance(self.operation_name, duration)
        else:
            # Operation failed - log error with duration
            self.logger.error(
                f"Operation '{self.operation_name}' failed after {duration:.3f}s",
                exc_info=(exc_type, exc_val, exc_tb)
            )


def log_function_call(logger: Optional[NukeLogger] = None, 
                      level: str = LOG_DEBUG):
    """
    Decorator to log function calls with arguments and results
    
    Args:
        logger: Logger instance (uses default if None)
        level: Logging level for function calls
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            func_name = func.__name__
            
            # Log function call with arguments
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




