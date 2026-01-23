# import nuke
# from typing import Tuple, List, Dict, Set, Optional, Union

# def get_nuke_version() -> Tuple[int, int, str, int]:
#     """
#     Get the current Nuke version details.
#     Return:
#         MAJOR_VER : int
#         MINOR_VER : int
#         STRING    : str
#         RELEASE   : int
#     """

#     major = nuke.NUKE_VERSION_MAJOR
#     minor = nuke.NUKE_VERSION_MINOR
#     string = nuke.NUKE_VERSION_STRING
#     release = nuke.NUKE_VERSION_RELEASE

#     return major, minor, string, release

# def is_gui() -> bool:
#     """
#     Check whether Nuke is running in GUI mode.

#     Return:
#         is_gui : bool
#     """
#     is_gui = nuke.env.get('gui')

#     return is_gui


# def get_threads() -> Optional[int]:
#     """
#     Get the number of threads Nuke is configured to use.

#     Return :
#         thread_value : int
#     """
#     thread_value = nuke.env.get('threads')

#     return thread_value

# def get_cpu_count() -> Optional[int]:
#     """
#     Get the number of CPUs available to Nuke.

#     Return:
#         cpu_count : int 
#     """
#     cpu_count = nuke.env.get('numCPUs')

#     return cpu_count

# def get_executable_path() -> Optional[str]:
#     """
#     Get the Nuke executable path.

#     Return:
#         exe_path = str
#     """
#     exe_path = nuke.env.get('ExecutablePath')

#     return exe_path

# def get_current_script_path() -> str:
#     """
#     Get the current Nuke script path.

#     Return:
#         cur_script_path : str
#     """
#     cur_script_path = nuke.root().name()

#     return cur_script_path

# def get_existing_channels() -> List[str]:
#     """
#     Get all existing channels in the current Nuke script.

#     Return:
#         channels_lst : list
#     """
#     channels_lst = nuke.root().channels()

#     return channels_lst


# def is_script_saved() -> bool:
#     """
#     Check whether the current Nuke script is saved.

#     Returns:
#         bool: True if the script has been saved, False otherwise.
#     """
#     script_path = nuke.root().name()

#     if script_path and script_path != "Root":
#         return True
#     else:
#         return False

###################################################

import os
import sys
import platform
import json
import yaml
import subprocess
import tempfile
import shutil
from pathlib import Path, PurePath
from typing import Dict, List, Optional, Tuple, Union, Any
import logging

# Import constants
# from . import constants

# Setup logging
logger = logging.getLogger(__name__)


class NukeEnvironment:
    """Main environment manager for Nuke pipeline."""
    
    def __init__(self):
        self._env_cache = {}
        self._path_cache = {}
        self._system_info = None
        self._user_info = None
        self._project_info = None
        self._initialized = False
        
        # Initialize on creation
        self._initialize()
    
    def _initialize(self):
        """Initialize the environment manager."""
        if self._initialized:
            return
        
        logger.info("Initializing Nuke environment manager...")
        
        # Gather system information
        self._gather_system_info()
        
        # Gather user information
        self._gather_user_info()
        
        # Setup default paths
        self._setup_default_paths()
        
        # Validate environment
        self._validate_environment()
        
        # Load project configuration if available
        self._load_project_config()
        
        self._initialized = True
        logger.info("Nuke environment manager initialized successfully")
    
    
    def _gather_system_info(self):
        """Gather system information."""
        self._system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'nuke_version': self.get_nuke_version(),
            'nuke_path': self.get_nuke_executable(),
            'hostname': platform.node(),
            'cpu_count': os.cpu_count(),
            'total_memory': self._get_total_memory(),
            'available_memory': self._get_available_memory(),
        }
    
    def _get_total_memory(self) -> int:
        """Get total system memory in MB."""
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory.restype = ctypes.c_ulonglong
                memory = ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory()
                return memory // 1024
            elif platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            return int(line.split()[1]) // 1024
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                      capture_output=True, text=True)
                return int(result.stdout.strip()) // 1024 // 1024
        except:
            pass
        return 0
    
    def _get_available_memory(self) -> int:
        """Get available system memory in MB."""
        try:
            if platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                    meminfo = {}
                    for line in lines:
                        key, value = line.split(':')
                        meminfo[key.strip()] = int(value.split()[0])
                    available = meminfo.get('MemAvailable', 0)
                    return available // 1024
        except:
            pass
        return self._system_info.get('total_memory', 0) if self._system_info else 0
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information dictionary."""
        return self._system_info.copy()
    
    def print_system_info(self):
        """Print system information to console."""
        if not self._system_info:
            return
        
        print("\n" + "="*60)
        print("SYSTEM INFORMATION")
        print("="*60)
        for key, value in self._system_info.items():
            print(f"{key:30}: {value}")
        print("="*60)
    
    def _gather_user_info(self):
        """Gather user information."""
        self._user_info = {
            'username': self.get_username(),
            'user_id': self.get_user_id(),
            'home_directory': str(Path.home()),
            'documents_directory': str(Path.home() / "Documents"),
            'desktop_directory': str(Path.home() / "Desktop"),
            'is_admin': self.is_admin(),
            'is_developer': self.is_developer(),
            'groups': self.get_user_groups(),
        }
    
    def get_username(self) -> str:
        """Get current username."""
        # Try environment variables first
        username = (
            os.environ.get('USER') or
            os.environ.get('USERNAME') or
            os.environ.get('LOGNAME') or
            os.environ.get('NUKE_USER') or
            "unknown_user"
        )
        return username
    
    def get_user_id(self) -> int:
        """Get current user ID."""
        try:
            import pwd
            return pwd.getpwuid(os.getuid()).pw_uid
        except:
            return 0
    
    def is_admin(self) -> bool:
        """Check if current user has admin privileges."""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def is_developer(self) -> bool:
        """Check if current user is a developer."""
        username = self.get_username()
        dev_users = self.get_env_list('NUKE_DEV_USERS', ['admin', 'developer', 'td'])
        return username.lower() in dev_users or 'dev' in username.lower()
    
    def get_user_groups(self) -> List[str]:
        """Get user groups (Unix-like systems)."""
        try:
            import grp
            groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
            return groups
        except:
            return []
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get user information dictionary."""
        return self._user_info.copy()
    
    
    def _setup_default_paths(self):
        """Setup default path configurations."""
        # Base directories
        self._path_cache['home'] = str(Path.home())
        self._path_cache['temp'] = tempfile.gettempdir()
        self._path_cache['cwd'] = os.getcwd()
        
        # Nuke specific paths
        nuke_path = self.get_env('NUKE_PATH', '')
        if nuke_path:
            self._path_cache['nuke_path'] = nuke_path
            nuke_paths = nuke_path.split(os.pathsep)
            self._path_cache['nuke_paths'] = nuke_paths
        
        # Python paths
        python_path = os.environ.get('PYTHONPATH', '')
        if python_path:
            self._path_cache['python_path'] = python_path
            python_paths = python_path.split(os.pathsep)
            self._path_cache['python_paths'] = python_paths
        
        # Custom pipeline paths
        self._setup_pipeline_paths()
    
    def _setup_pipeline_paths(self):
        """Setup pipeline-specific paths."""
        # Project root
        project_root = self.get_env('PROJECT_ROOT')
        if project_root:
            self._path_cache['project_root'] = project_root
            
            # Define subdirectories based on project root
            subdirs = {
                'assets': 'assets',
                'shots': 'shots',
                'sequences': 'sequences',
                'renders': 'renders',
                'plates': 'plates',
                'references': 'references',
                'scripts': 'scripts',
                'config': 'config',
                'tools': 'tools',
                'temp': 'temp',
                'logs': 'logs',
            }
            
            for key, subdir in subdirs.items():
                path = Path(project_root) / subdir
                self._path_cache[f'project_{key}'] = str(path)
        
        # Show/Shot specific paths
        show = self.get_env('SHOW')
        shot = self.get_env('SHOT')
        
        if show and shot:
            shot_path = f"{show}/{shot}"
            self._path_cache['shot_path'] = shot_path
            
            # Shot subdirectories
            shot_dirs = {
                'comp': 'comp',
                'roto': 'roto',
                'paint': 'paint',
                'track': 'track',
                'render': 'render',
                'plate': 'plate',
                'reference': 'reference',
                'review': 'review',
            }
            
            for key, subdir in shot_dirs.items():
                path = Path(project_root or '') / 'shots' / show / shot / subdir
                self._path_cache[f'shot_{key}'] = str(path)
    
    def get_path(self, key: str, default: str = None) -> Optional[str]:
        """Get a cached path by key."""
        return self._path_cache.get(key, default)
    
    def set_path(self, key: str, path: str):
        """Set a path in cache."""
        self._path_cache[key] = path
    
    def resolve_path(self, path: str) -> str:
        """
        Resolve a path with environment variables and user expansion.
        
        Args:
            path: Path string that may contain env vars or ~
            
        Returns:
            Resolved absolute path
        """
        # Expand user home
        if path.startswith('~'):
            path = os.path.expanduser(path)
        
        # Expand environment variables
        path = os.path.expandvars(path)
        
        # Convert to absolute path
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        return path
    
    def find_file(self, filename: str, search_paths: List[str] = None) -> Optional[str]:
        """
        Find a file in search paths.
        
        Args:
            filename: File to find
            search_paths: List of paths to search (defaults to NUKE_PATH)
            
        Returns:
            Full path to file or None if not found
        """
        if search_paths is None:
            search_paths = self._path_cache.get('nuke_paths', [])
        
        for search_path in search_paths:
            if not search_path:
                continue
            
            full_path = Path(search_path) / filename
            if full_path.exists():
                return str(full_path)
            
            # Also check with .nk extension if not provided
            if not filename.endswith('.nk'):
                full_path = Path(search_path) / f"{filename}.nk"
                if full_path.exists():
                    return str(full_path)
        
        return None
    
    def ensure_directory(self, path: str) -> bool:
        """
        Ensure a directory exists, create if it doesn't.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable with caching.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value
        """
        # Check cache first
        if key in self._env_cache:
            return self._env_cache[key]
        
        # Get from environment
        value = os.environ.get(key, default)
        
        # Cache the value
        self._env_cache[key] = value
        
        return value
    
    def set_env(self, key: str, value: Any, persistent: bool = False):
        """
        Set environment variable.
        
        Args:
            key: Environment variable name
            value: Value to set
            persistent: If True, also set in os.environ
        """
        # Update cache
        self._env_cache[key] = value
        
        # Update environment if persistent
        if persistent:
            os.environ[key] = str(value)
            
            # Also update for subprocesses
            if platform.system() == "Windows":
                # This would require registry modification for true persistence
                pass
    
    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = self.get_env(key, str(default)).lower()
        return value in ('true', 'yes', '1', 'on', 't')
    
    def get_env_int(self, key: str, default: int = 0) -> int:
        """Get environment variable as integer."""
        try:
            return int(self.get_env(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_env_float(self, key: str, default: float = 0.0) -> float:
        """Get environment variable as float."""
        try:
            return float(self.get_env(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_env_list(self, key: str, default: List = None, separator: str = os.pathsep) -> List[str]:
        """Get environment variable as list."""
        if default is None:
            default = []
        
        value = self.get_env(key, '')
        if not value:
            return default
        
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def get_env_dict(self, key: str, default: Dict = None) -> Dict:
        """Get environment variable as JSON dictionary."""
        if default is None:
            default = {}
        
        value = self.get_env(key, '')
        if not value:
            return default
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from {key}")
            return default
    
    def append_env_path(self, key: str, path: str, position: str = 'end'):
        """
        Append a path to an environment path variable.
        
        Args:
            key: Environment variable name (e.g., 'NUKE_PATH')
            path: Path to append
            position: 'beginning' or 'end'
        """
        current = self.get_env(key, '')
        paths = [p.strip() for p in current.split(os.pathsep) if p.strip()]
        
        # Remove if already exists
        if path in paths:
            paths.remove(path)
        
        # Add at specified position
        if position == 'beginning':
            paths.insert(0, path)
        else:  # 'end'
            paths.append(path)
        
        # Update environment
        new_value = os.pathsep.join(paths)
        self.set_env(key, new_value, persistent=True)
    
    
    def get_nuke_version(self) -> str:
        """Get Nuke version string."""
        try:
            # Try to get from Nuke's internal module
            import nuke
            return nuke.NUKE_VERSION_STRING
        except ImportError:
            # Fall back to environment variable
            return self.get_env('NUKE_VERSION', 'Unknown')
    
    def get_nuke_executable(self) -> Optional[str]:
        """Get path to Nuke executable."""
        # Try various environment variables
        nuke_exe = (
            self.get_env('NUKE_EXECUTABLE') or
            self.get_env('NUKE_LOCATION') or
            shutil.which('nuke') or
            shutil.which('Nuke')
        )
        
        if nuke_exe and Path(nuke_exe).exists():
            return nuke_exe
        
        # Platform-specific default locations
        if platform.system() == "Windows":
            defaults = [
                r"C:\Program Files\Nuke15.1v3\Nuke15.1.exe",
                r"C:\Program Files\Nuke15.1\Nuke15.1.exe",
            ]
        elif platform.system() == "Darwin":  # macOS
            defaults = [
                "/Applications/Nuke15.1v3/Nuke15.1v3.app/Contents/MacOS/Nuke15.1v3",
                "/Applications/Nuke15.1/Nuke15.1.app/Contents/MacOS/Nuke15.1",
            ]
        else:  # Linux
            defaults = [
                "/usr/local/Nuke15.1v3/Nuke15.1v3",
                "/usr/local/Nuke15.1/Nuke15.1",
            ]
        
        for default in defaults:
            if Path(default).exists():
                return default
        
        return None
    
    def get_ocio_config(self) -> Optional[str]:
        """Get OCIO config path."""
        ocio_config = self.get_env('OCIO')
        if ocio_config and Path(ocio_config).exists():
            return ocio_config
        
        # Look for common locations
        common_locations = [
            '/usr/local/share/ocio/configs',
            '/opt/ocio/configs',
            str(Path.home() / 'ocio' / 'configs'),
        ]
        
        for location in common_locations:
            config_path = Path(location) / 'config.ocio'
            if config_path.exists():
                return str(config_path)
        
        return None
    
    def get_nuke_temp_dir(self) -> str:
        """Get Nuke temp directory."""
        temp_dir = self.get_env('NUKE_TEMP_DIR')
        if temp_dir:
            return temp_dir
        
        # Default temp directory with nuke subfolder
        default_temp = Path(tempfile.gettempdir()) / 'nuke'
        default_temp.mkdir(exist_ok=True)
        
        return str(default_temp)
    
    def get_plugin_paths(self) -> List[str]:
        """Get Nuke plugin paths."""
        plugin_paths = []
        
        # NUKE_PATH
        nuke_path = self.get_env('NUKE_PATH', '')
        if nuke_path:
            for path in nuke_path.split(os.pathsep):
                if path:
                    plugin_dir = Path(path) / 'plugins'
                    if plugin_dir.exists():
                        plugin_paths.append(str(plugin_dir))
        
        # User plugin directory
        user_plugin_dir = Path.home() / '.nuke' / 'plugins'
        if user_plugin_dir.exists():
            plugin_paths.append(str(user_plugin_dir))
        
        return plugin_paths
    
    def get_gizmo_paths(self) -> List[str]:
        """Get Nuke gizmo paths."""
        gizmo_paths = []
        
        # NUKE_GIZMO_PATH
        gizmo_path = self.get_env('NUKE_GIZMO_PATH', '')
        if gizmo_path:
            for path in gizmo_path.split(os.pathsep):
                if path:
                    gizmo_paths.append(path)
        
        # NUKE_PATH subdirectories
        nuke_path = self.get_env('NUKE_PATH', '')
        if nuke_path:
            for path in nuke_path.split(os.pathsep):
                if path:
                    gizmo_dir = Path(path) / 'gizmos'
                    if gizmo_dir.exists():
                        gizmo_paths.append(str(gizmo_dir))
        
        # User gizmo directory
        user_gizmo_dir = Path.home() / '.nuke' / 'gizmos'
        if user_gizmo_dir.exists():
            gizmo_paths.append(str(user_gizmo_dir))
        
        return gizmo_paths
    
    
    def _load_project_config(self):
        """Load project configuration if available."""
        project_config = self.find_file('project_config.json')
        if project_config:
            try:
                with open(project_config, 'r') as f:
                    self._project_info = json.load(f)
                logger.info(f"Loaded project config: {project_config}")
            except Exception as e:
                logger.error(f"Failed to load project config: {e}")
        
        # Also try YAML
        if not self._project_info:
            project_config = self.find_file('project_config.yaml')
            if not project_config:
                project_config = self.find_file('project_config.yml')
            
            if project_config:
                try:
                    with open(project_config, 'r') as f:
                        self._project_info = yaml.safe_load(f)
                    logger.info(f"Loaded project config: {project_config}")
                except Exception as e:
                    logger.error(f"Failed to load project config: {e}")
    
    def get_project_config(self, key: str = None, default: Any = None) -> Any:
        """
        Get project configuration value.
        
        Args:
            key: Configuration key (dot notation for nested)
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        if not self._project_info:
            return default
        
        if key is None:
            return self._project_info
        
        # Handle dot notation for nested keys
        value = self._project_info
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def set_project_config(self, key: str, value: Any):
        """
        Set project configuration value.
        
        Args:
            key: Configuration key (dot notation for nested)
            value: Value to set
        """
        if self._project_info is None:
            self._project_info = {}
        
        # Handle dot notation for nested keys
        keys = key.split('.')
        target = self._project_info
        
        for part in keys[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        
        target[keys[-1]] = value
    
    def save_project_config(self, path: str = None):
        """Save project configuration to file."""
        if not self._project_info:
            logger.warning("No project configuration to save")
            return False
        
        if path is None:
            # Try to find existing config file
            path = self.find_file('project_config.json')
            if not path:
                path = self.find_file('project_config.yaml')
                if not path:
                    path = self.find_file('project_config.yml')
                    if not path:
                        # Create new file in project root
                        project_root = self.get_path('project_root', os.getcwd())
                        path = str(Path(project_root) / 'project_config.json')
        
        try:
            with open(path, 'w') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    yaml.dump(self._project_info, f, default_flow_style=False)
                else:
                    json.dump(self._project_info, f, indent=2)
            
            logger.info(f"Saved project config to: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save project config: {e}")
            return False
    
    def _validate_environment(self):
        """Validate the environment setup."""
        warnings = []
        errors = []
        
        # Check required environment variables
        required_envs = self.get_env_list('NUKE_REQUIRED_ENV', [
            'NUKE_PATH',
            'PROJECT_ROOT'
        ])
        
        for env_var in required_envs:
            if not self.get_env(env_var):
                warnings.append(f"Environment variable {env_var} is not set")
        
        # Check Nuke executable
        nuke_exe = self.get_nuke_executable()
        if not nuke_exe:
            warnings.append("Nuke executable not found")
        
        # Check write permissions for temp directory
        temp_dir = self.get_nuke_temp_dir()
        try:
            test_file = Path(temp_dir) / '.write_test'
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"Cannot write to temp directory {temp_dir}: {e}")
        
        # Log warnings and errors
        if warnings:
            logger.warning("Environment validation warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        if errors:
            logger.error("Environment validation errors:")
            for error in errors:
                logger.error(f"  - {error}")
            
            if self.get_env_bool('NUKE_STRICT_VALIDATION', False):
                raise EnvironmentError("Environment validation failed")
    
    def validate_path(self, path: str, check_write: bool = False) -> Tuple[bool, str]:
        """
        Validate a path.
        
        Args:
            path: Path to validate
            check_write: Check write permissions
            
        Returns:
            Tuple of (is_valid, message)
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, f"Path does not exist: {path}"
        
        if check_write:
            try:
                test_file = path_obj / '.write_test'
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                return False, f"No write permission: {path}"
            except Exception as e:
                return False, f"Write test failed: {e}"
        
        return True, "Path is valid"
    
     
    def export_environment(self, format: str = 'dict') -> Union[Dict, str]:
        """
        Export environment as dictionary or string.
        
        Args:
            format: 'dict', 'json', or 'shell'
            
        Returns:
            Environment representation
        """
        env_dict = {
            'system': self._system_info,
            'user': self._user_info,
            'paths': self._path_cache,
            'project': self._project_info,
            'environment': dict(os.environ),
        }
        
        if format == 'dict':
            return env_dict
        elif format == 'json':
            return json.dumps(env_dict, indent=2, default=str)
        elif format == 'shell':
            # Export as shell commands
            lines = []
            for key, value in os.environ.items():
                if key.startswith('NUKE_') or key in ['PROJECT_ROOT', 'SHOW', 'SHOT']:
                    lines.append(f'export {key}="{value}"')
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def create_environment_report(self, output_file: str = None) -> str:
        """
        Create a comprehensive environment report.
        
        Args:
            output_file: File to write report to (optional)
            
        Returns:
            Report as string
        """
        report = []
        
        # Header
        report.append("="*80)
        report.append("NUKE ENVIRONMENT REPORT")
        report.append("="*80)
        
        # System Information
        report.append("\nSYSTEM INFORMATION:")
        report.append("-"*40)
        for key, value in self._system_info.items():
            report.append(f"{key:25}: {value}")
        
        # User Information
        report.append("\nUSER INFORMATION:")
        report.append("-"*40)
        for key, value in self._user_info.items():
            report.append(f"{key:25}: {value}")
        
        # Paths
        report.append("\nIMPORTANT PATHS:")
        report.append("-"*40)
        for key in sorted(self._path_cache.keys()):
            if 'path' in key.lower() or 'dir' in key.lower():
                report.append(f"{key:25}: {self._path_cache[key]}")
        
        # Environment Variables
        report.append("\nNUKE ENVIRONMENT VARIABLES:")
        report.append("-"*40)
        nuke_envs = {k: v for k, v in os.environ.items() 
                    if k.startswith('NUKE_') or 'NUKE' in k.upper()}
        for key, value in sorted(nuke_envs.items()):
            report.append(f"{key:25}: {value}")
        
        # Project Configuration
        if self._project_info:
            report.append("\nPROJECT CONFIGURATION:")
            report.append("-"*40)
            report.append(json.dumps(self._project_info, indent=2, default=str))
        
        report_text = '\n'.join(report)
        
        # Write to file if specified
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                logger.info(f"Environment report saved to: {output_file}")
            except Exception as e:
                logger.error(f"Failed to save environment report: {e}")
        
        return report_text
    
    def cleanup_temp_files(self, older_than_days: int = 7):
        """
        Clean up temporary files older than specified days.
        
        Args:
            older_than_days: Delete files older than this many days
        """
        import time
        import datetime
        
        temp_dir = self.get_nuke_temp_dir()
        current_time = time.time()
        cutoff = current_time - (older_than_days * 24 * 60 * 60)
        
        deleted_count = 0
        total_size = 0
        
        for item in Path(temp_dir).rglob('*'):
            if item.is_file():
                try:
                    file_time = item.stat().st_mtime
                    if file_time < cutoff:
                        file_size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        total_size += file_size
                except Exception as e:
                    logger.warning(f"Failed to delete {item}: {e}")
        
        if deleted_count > 0:
            total_size_mb = total_size / (1024 * 1024)
            logger.info(f"Cleaned up {deleted_count} temp files ({total_size_mb:.2f} MB)")
    
    def reload_environment(self):
        """Reload environment configuration."""
        self._env_cache.clear()
        self._path_cache.clear()
        self._system_info = None
        self._user_info = None
        self._project_info = None
        self._initialized = False
        self._initialize()


# Global environment instance
_env_instance = None

def get_env() -> NukeEnvironment:
    """Get the global environment instance."""
    global _env_instance
    if _env_instance is None:
        _env_instance = NukeEnvironment()
    return _env_instance

def reload_env():
    """Reload the global environment."""
    global _env_instance
    if _env_instance:
        _env_instance.reload_environment()
    else:
        _env_instance = NukeEnvironment()

# Helper functions for common operations
def get_project_root() -> str:
    """Get project root directory."""
    return get_env().get_env('PROJECT_ROOT')

def get_show() -> str:
    """Get current show."""
    return get_env().get_env('SHOW')

def get_shot() -> str:
    """Get current shot."""
    return get_env().get_env('SHOT')

def get_task() -> str:
    """Get current task."""
    return get_env().get_env('TASK')

def get_dept() -> str:
    """Get current department."""
    return get_env().get_env('DEPT')

def get_shot_path() -> str:
    """Get current shot path."""
    show = get_show()
    shot = get_shot()
    if show and shot:
        return f"{show}/{shot}"
    return ""

def get_asset_path(asset_type: str, asset_name: str) -> str:
    """Get path for an asset."""
    project_root = get_project_root()
    if not project_root:
        return ""
    
    return str(Path(project_root) / 'assets' / asset_type / asset_name)

def get_sequence_path(sequence: str) -> str:
    """Get path for a sequence."""
    project_root = get_project_root()
    if not project_root:
        return ""
    
    return str(Path(project_root) / 'sequences' / sequence)

def is_production() -> bool:
    """Check if running in production environment."""
    return get_env().get_env_bool('NUKE_PRODUCTION', False)

def is_development() -> bool:
    """Check if running in development environment."""
    return get_env().get_env_bool('NUKE_DEVELOPMENT', True)

def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return get_env().get_env_bool('NUKE_DEBUG', False)

def get_ocio_config_path() -> str:
    """Get OCIO config path."""
    return get_env().get_ocio_config() or ""

def get_nuke_temp_path() -> str:
    """Get Nuke temp directory path."""
    return get_env().get_nuke_temp_dir()


def setup_environment(project_root: str = None, show: str = None, 
                     shot: str = None, task: str = None, dept: str = None):
    """
    Setup the pipeline environment.
    
    Args:
        project_root: Project root directory
        show: Show name
        shot: Shot name
        task: Task name
        dept: Department name
    """
    env = get_env()
    
    # Set environment variables
    if project_root:
        env.set_env('PROJECT_ROOT', project_root, persistent=True)
    
    if show:
        env.set_env('SHOW', show, persistent=True)
    
    if shot:
        env.set_env('SHOT', shot, persistent=True)
    
    if task:
        env.set_env('TASK', task, persistent=True)
    
    if dept:
        env.set_env('DEPT', dept, persistent=True)
    
    # Setup paths based on new environment
    env._setup_pipeline_paths()
    
    logger.info(f"Environment setup: project={project_root}, show={show}, shot={shot}")

def initialize_pipeline():
    """Initialize the entire pipeline environment."""
    env = get_env()
    
    # Print welcome message
    logger.info("Initializing Nuke Pipeline Environment...")
    
    # Create required directories
    required_dirs = [
        env.get_path('project_temp'),
        env.get_path('project_logs'),
        env.get_path('project_config'),
        env.get_nuke_temp_dir(),
    ]
    
    for dir_path in required_dirs:
        if dir_path:
            env.ensure_directory(dir_path)
    
    # Setup Python path
    python_paths = []
    
    # Add project tools directory
    tools_dir = env.get_path('project_tools')
    if tools_dir:
        python_paths.append(tools_dir)
    
    # Add user .nuke directory
    user_nuke_dir = Path.home() / '.nuke'
    if user_nuke_dir.exists():
        python_paths.append(str(user_nuke_dir))
    
    # Update PYTHONPATH
    if python_paths:
        current_pythonpath = env.get_env('PYTHONPATH', '')
        for path in python_paths:
            if path not in current_pythonpath:
                env.append_env_path('PYTHONPATH', path)
    
    # Create environment report
    report_file = env.get_path('project_logs', '')
    if report_file:
        report_file = str(Path(report_file) / 'environment_report.txt')
        env.create_environment_report(report_file)
    
    logger.info("Pipeline environment initialized successfully")



if __name__ == "__main__":
    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Create and test environment manager
    env = NukeEnvironment()
    
    # Print system info
    env.print_system_info()
    
    # Print environment report
    print(env.create_environment_report())