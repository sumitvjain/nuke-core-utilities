import os
import sys
from pathlib import Path

# ============================================================================
# FILE SYSTEM & PATHS
# ============================================================================

# Directory names
DIR_SCRIPTS = "scripts"
DIR_PLUGINS = "plugins"
DIR_PYTHON = "python"
DIR_ICONS = "icons"
DIR_GIZMOS = "gizmos"
DIR_TOOLS = "tools"
DIR_CONFIG = "config"
DIR_TEMP = "temp"
DIR_BACKUP = "backup"
DIR_DOCS = "docs"
DIR_EXAMPLES = "examples"
DIR_TESTS = "tests"
DIR_LOG = "logs"

# File extensions
EXT_NK = ".nk"
EXT_GIZMO = ".gizmo"
EXT_PY = ".py"
EXT_JSON = ".json"
EXT_YAML = ".yaml"
EXT_YML = ".yml"
EXT_XML = ".xml"
EXT_TXT = ".txt"
EXT_LOG = ".log"
EXT_ICON = ".png"
EXT_EXR = ".exr"
EXT_DNX = ".mov"
EXT_MP4 = ".mp4"
EXT_JPG = ".jpg"
EXT_PNG = ".png"
EXT_TGA = ".tga"

# Special directories
NUKE_PATH = os.environ.get("NUKE_PATH", "")
NUKE_TEMP_DIR = os.environ.get("NUKE_TEMP_DIR", "/tmp")
HOME_DIR = str(Path.home())
DOCUMENTS_DIR = str(Path.home() / "Documents")



# Node classes
NODE_READ = "Read"
NODE_WRITE = "Write"
NODE_VIEWER = "Viewer"
NODE_DOT = "Dot"
NODE_BACKDROP = "BackdropNode"
NODE_STICKY = "StickyNote"
NODE_MERGE = "Merge2"
NODE_TRANSFORM = "Transform"
NODE_ROTO = "Roto"
NODE_ROTOPAINT = "RotoPaint"
NODE_GRADE = "Grade"
NODE_COLORCORRECT = "ColorCorrect"
NODE_SCANLINE = "ScanlineRender"
NODE_CAMERA = "Camera3"
NODE_AXIS = "Axis3"
NODE_GEOMETRY = "ReadGeo2"

# Viewer states
VIEWER_FRAME = "frame"
VIEWER_PROXY = "proxy"
VIEWER_LUT = "viewerLUT"
VIEWER_INPUT = "viewerInput"
VIEWER_PROCESS = "viewerProcess"

# Project settings
PROJECT_FPS = "fps"
PROJECT_FRANGE = "frame_range"
PROJECT_FSTART = "first_frame"
PROJECT_FEND = "last_frame"
PROJECT_RESOLUTION = "root.format"
PROJECT_LUT = "colorLUT"


# Tile colors (Nuke color format: 0xRRGGBBAA)
COLOR_RED = 0xFF0000FF
COLOR_GREEN = 0x00FF00FF
COLOR_BLUE = 0x0000FFFF
COLOR_YELLOW = 0xFFFF00FF
COLOR_ORANGE = 0xFF8000FF
COLOR_PURPLE = 0x8000FFFF
COLOR_CYAN = 0x00FFFFFF
COLOR_PINK = 0xFF00FFFF
COLOR_GRAY = 0x808080FF
COLOR_WHITE = 0xFFFFFFFF
COLOR_BLACK = 0x000000FF

# Node type colors
COLOR_INPUT = COLOR_GREEN
COLOR_OUTPUT = COLOR_RED
COLOR_EFFECT = COLOR_BLUE
COLOR_TRANSFORM = COLOR_YELLOW
COLOR_3D = COLOR_PURPLE
COLOR_UTILITY = COLOR_GRAY
COLOR_GROUP = COLOR_ORANGE
COLOR_SCRIPT = COLOR_CYAN

# Backdrop colors
BACKDROP_DEFAULT = 0x404040FF
BACKDROP_WARNING = 0xFF4000FF
BACKDROP_INFO = 0x0040FFFF
BACKDROP_SUCCESS = 0x40FF00FF
BACKDROP_IMPORTANT = 0xFF00FFFF


# Pipeline stages
STAGE_PREPROD = "preproduction"
STAGE_PROD = "production"
STAGE_POST = "postproduction"
STAGE_VFX = "vfx"
STAGE_ANIM = "animation"
STAGE_LIGHTING = "lighting"
STAGE_COMP = "compositing"
STAGE_ROTO = "roto"
STAGE_PAINT = "paint"
STAGE_TRACK = "tracking"

# Departments
DEPT_COMP = "comp"
DEPT_LIGHTING = "lighting"
DEPT_ANIM = "anim"
DEPT_MODEL = "model"
DEPT_RIG = "rig"
DEPT_FX = "fx"
DEPT_MATTE = "matte"
DEPT_ROTO = "roto"

# Task types
TASK_COMP = "comp"
TASK_PREP = "prep"
TASK_KEY = "key"
TASK_CLEANUP = "cleanup"
TASK_TRACK = "track"
TASK_PAINT = "paint"
TASK_ROTO = "roto"
TASK_SETUP = "setup"
TASK_RENDER = "render"
TASK_REVIEW = "review"

# Review states
REVIEW_WIP = "wip"
REVIEW_CLIENT = "client"
REVIEW_INTERNAL = "internal"
REVIEW_APPROVED = "approved"
REVIEW_FINAL = "final"


# Render formats
RENDER_EXR = "exr"
RENDER_TIFF = "tiff"
RENDER_JPEG = "jpeg"
RENDER_PNG = "png"
RENDER_DPX = "dpx"
RENDER_TARGA = "targa"
RENDER_MOV = "mov"
RENDER_MP4 = "mp4"

# EXR compression
EXR_NONE = "none"
EXR_RLE = "rle"
EXR_ZIPS = "zips"
EXR_ZIP = "zip"
EXR_PIZ = "piz"
EXR_PXR24 = "pxr24"
EXR_B44 = "b44"
EXR_B44A = "b44a"
EXR_DWAA = "dwaa"
EXR_DWAB = "dwab"

# Channels
CHANNEL_RGB = "rgb"
CHANNEL_RGBA = "rgba"
CHANNEL_R = "red"
CHANNEL_G = "green"
CHANNEL_B = "blue"
CHANNEL_A = "alpha"
CHANNEL_Z = "depth"
CHANNEL_N = "normal"
CHANNEL_UV = "uv"

# Common resolutions
RES_HD = "1920x1080"
RES_2K = "2048x1152"
RES_UHD = "3840x2160"
RES_4K = "4096x2304"
RES_8K = "8192x4608"
RES_SQ_2K = "2048x2048"
RES_SQ_4K = "4096x4096"


# Error codes
ERROR_FILE_NOT_FOUND = 1001
ERROR_NODE_NOT_FOUND = 1002
ERROR_INVALID_FORMAT = 1003
ERROR_MISSING_INPUT = 1004
ERROR_RENDER_FAILED = 1005
ERROR_SCRIPT_ERROR = 1006
ERROR_PERMISSION_DENIED = 1007
ERROR_DISK_FULL = 1008
ERROR_LICENSE = 1009
ERROR_MEMORY = 1010

# Warning codes
WARNING_DEPRECATED = 2001
WARNING_PERFORMANCE = 2002
WARNING_DISK_SPACE = 2003
WARNING_VERSION_MISMATCH = 2004
WARNING_SETTINGS = 2005
WARNING_CACHE = 2006

# Info codes
INFO_STARTUP = 3001
INFO_SHUTDOWN = 3002
INFO_RENDER_START = 3003
INFO_RENDER_END = 3004
INFO_SAVE = 3005
INFO_LOAD = 3006

# REGEX PATTERNS
REGEX_VERSION = r"v(\d+)(?:\.(\d+))?(?:\.(\d+))?"
REGEX_SEQUENCE = r"\.(\d+)(?:-(\d+))?\."
REGEX_SHOW = r"([a-zA-Z]+)_([a-zA-Z]+)"
REGEX_SHOT = r"([a-zA-Z]+)_(\d+)([a-zA-Z]*)"
REGEX_TASK = r"_([a-z]+)_"
REGEX_USER = r"([a-zA-Z]+)\.([a-zA-Z]+)"
REGEX_FRAME = r"%0(\d)d"
REGEX_EXTENSION = r"\.([a-zA-Z0-9]+)$"
REGEX_COLOR = r"0x([A-Fa-f0-9]{8})"
REGEX_NUKE_VERSION = r"(\d+)\.(\d+)v(\d+)"

# Default values
DEFAULT_FPS = 24
DEFAULT_FRAME_RANGE = "1-100"
DEFAULT_COLORSPACE = "sRGB"
DEFAULT_FORMAT = "1920x1080"
DEFAULT_TILE_COLOR = 0x0
DEFAULT_LUT = "sRGB"
DEFAULT_PROXY_SCALE = 0.5
DEFAULT_CACHE_SIZE = 2048  # MB
DEFAULT_UNDO_STEPS = 50

# Limits
MAX_NODES = 10000
MAX_VIEWERS = 4
MAX_CURVES = 1000
MAX_CHANNELS = 1024
MAX_FRAME_BUFFER = 100
MAX_STRING_LENGTH = 1024
MAX_ARRAY_SIZE = 1000000
MAX_RECURSION_DEPTH = 100

# Menu paths
MENU_FILE = "File"
MENU_EDIT = "Edit"
MENU_VIEWER = "Viewer"
MENU_RENDER = "Render"
MENU_TOOLSET = "ToolSets"
MENU_SCRIPTS = "Scripts"
MENU_PLUGINS = "Plugins"
MENU_DEBUG = "Debug"
MENU_HELP = "Help"

# Toolset categories
TOOLSET_COMP = "Compositing"
TOOLSET_3D = "3D"
TOOLSET_KEY = "Keying"
TOOLSET_TRACK = "Tracking"
TOOLSET_PAINT = "Paint"
TOOLSET_ROTO = "Roto"
TOOLSET_UTILITY = "Utility"
TOOLSET_DEV = "Development"

# Pane names
PANE_NODE_GRAPH = "DAG"
PANE_PROPS = "Properties"
PANE_VIEWER = "Viewer"
PANE_CURVE = "Curve"
PANE_CONSOLE = "Script Editor"
PANE_ERRORS = "Error Console"
PANE_HISTORY = "History"
PANE_BROWSER = "File Browser"

# Log levels
LOG_DEBUG = "DEBUG"
LOG_INFO = "INFO"
LOG_WARNING = "WARNING"
LOG_ERROR = "ERROR"
LOG_CRITICAL = "CRITICAL"

# Log formats
LOG_FORMAT_SIMPLE = "%(levelname)s: %(message)s"
LOG_FORMAT_DETAILED = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_VERBOSE = "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"

# Log files
LOG_FILE_APP = "nuke_app.log"
LOG_FILE_ERROR = "nuke_error.log"
LOG_FILE_RENDER = "nuke_render.log"
LOG_FILE_DEBUG = "nuke_debug.log"
LOG_FILE_USER = "user_actions.log"

# Nuke versions
NUKE_VERSION_MAJOR = int(os.environ.get("NUKE_VERSION_MAJOR", 13))
NUKE_VERSION_MINOR = int(os.environ.get("NUKE_VERSION_MINOR", 0))
NUKE_VERSION = f"{NUKE_VERSION_MAJOR}.{NUKE_VERSION_MINOR}"

# Python versions
PYTHON_VERSION_MAJOR = sys.version_info.major
PYTHON_VERSION_MINOR = sys.version_info.minor
PYTHON_VERSION = f"{PYTHON_VERSION_MAJOR}.{PYTHON_VERSION_MINOR}"

# Compatibility flags
SUPPORT_PYTHON3 = PYTHON_VERSION_MAJOR >= 3
SUPPORT_NUKE13 = NUKE_VERSION_MAJOR >= 13
SUPPORT_OCIO2 = NUKE_VERSION_MAJOR >= 13
SUPPORT_USD = NUKE_VERSION_MAJOR >= 13


ENV_NUKE_PATH = "NUKE_PATH"
ENV_NUKE_TEMP_DIR = "NUKE_TEMP_DIR"
ENV_OCIO = "OCIO"
ENV_PYTHONPATH = "PYTHONPATH"
ENV_NUKE_INIT = "NUKE_INIT"
ENV_NUKE_GIZMO_PATH = "NUKE_GIZMO_PATH"
ENV_NUKE_FONT_PATH = "NUKE_FONT_PATH"
ENV_HOUND = "HOUND"  # For review submissions
ENV_SHOW = "SHOW"
ENV_SHOT = "SHOT"
ENV_USER = "USER"
ENV_TASK = "TASK"
ENV_DEPT = "DEPT"


# Template paths
TEMPLATE_NODE = "node_templates"
TEMPLATE_SCRIPT = "script_templates"
TEMPLATE_WORKFLOW = "workflow_templates"
TEMPLATE_RENDER = "render_templates"
TEMPLATE_PROJECT = "project_templates"

# Preset names
PRESET_FORMATS = "formats"
PRESET_LUTS = "luts"
PRESET_COLORS = "colors"
PRESET_SHORTCUTS = "shortcuts"
PRESET_LAYOUTS = "layouts"
PRESET_RENDER = "render_settings"


# Metadata keys
META_CREATOR = "creator"
META_CREATED = "created"
META_MODIFIED = "modified"
META_VERSION = "version"
META_DESCRIPTION = "description"
META_TAGS = "tags"
META_DEPARTMENT = "department"
META_SHOW = "show"
META_SHOT = "shot"
META_TASK = "task"
META_STATUS = "status"
META_ESTIMATE = "time_estimate"
META_ACTUAL = "time_actual"

# Custom knob names
CUSTOM_CREATED_BY = "created_by"
CUSTOM_VERSION = "custom_version"
CUSTOM_STATUS = "custom_status"
CUSTOM_NOTES = "notes"
CUSTOM_DEADLINE = "deadline"
CUSTOM_PRIORITY = "priority"
CUSTOM_REVIEW = "needs_review"


# Allowed file operations
ALLOWED_READ_EXT = [EXT_NK, EXT_PY, EXT_JSON, EXT_TXT, EXT_XML]
ALLOWED_WRITE_EXT = [EXT_NK, EXT_PY, EXT_JSON, EXT_TXT, EXT_XML, EXT_LOG]
ALLOWED_EXEC_EXT = [EXT_PY, EXT_GIZMO]

# Validation patterns
VALID_NODE_NAME = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
VALID_PYTHON_NAME = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
VALID_SHOW_NAME = r"^[a-zA-Z]{2,6}$"
VALID_SHOT_NAME = r"^[a-zA-Z]{2,6}_\d{3,4}[a-zA-Z]?$"
VALID_VERSION = r"^v\d{3,4}$"


def get_nuke_version_tuple():
    """Get Nuke version as tuple (major, minor, patch)."""
    return (NUKE_VERSION_MAJOR, NUKE_VERSION_MINOR, 0)


def is_nuke_version(major, minor=0):
    """Check if current Nuke version matches or is greater."""
    return (NUKE_VERSION_MAJOR, NUKE_VERSION_MINOR) >= (major, minor)


def get_color_hex(color_int):
    """Convert Nuke color integer to hex string."""
    return f"0x{color_int:08X}"


def get_resolution_tuple(res_str):
    """Convert resolution string to (width, height) tuple."""
    if "x" in res_str:
        w, h = res_str.split("x")
        return (int(w), int(h))
    return (1920, 1080)


# ============================================================================
# DEPRECATION WARNINGS
# ============================================================================

# Constants scheduled for removal
_DEPRECATED_CONSTANTS = {
    "OLD_FORMAT_NAME": "Use RES_HD instead",
    "LEGACY_COLOR": "Use COLOR_RED instead",
}

def check_deprecated(constant_name):
    """Warn about deprecated constants."""
    if constant_name in _DEPRECATED_CONSTANTS:
        import warnings
        warnings.warn(
            f"Constant '{constant_name}' is deprecated. {_DEPRECATED_CONSTANTS[constant_name]}",
            DeprecationWarning,
            stacklevel=2
        )