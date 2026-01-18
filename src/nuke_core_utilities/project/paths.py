"""
Project path management and resolution
"""

import os
import re
from pathlib import Path, PurePath
from typing import Dict, List, Optional, Tuple, Any
import nuke

from ..core.logging_utils import get_logger
from ..core.env import get_env
from ..core.constants import *

logger = get_logger(__name__)

class ProjectPaths:
    """Project path management and resolution"""
    
    def __init__(self):
        self.env = get_env()
        self.path_templates = {}
        self._load_path_templates()
    
    def _load_path_templates(self):
        """Load path templates"""
        self.path_templates = {
            'shot_comp': '{project}/shots/{show}/{shot}/comp/{task}',
            'shot_render': '{project}/shots/{show}/{shot}/render/{task}',
            'shot_plate': '{project}/shots/{show}/{shot}/plate',
            'shot_reference': '{project}/shots/{show}/{shot}/reference',
            'asset_texture': '{project}/assets/{asset_type}/{asset_name}/textures',
            'asset_model': '{project}/assets/{asset_type}/{asset_name}/model',
            'asset_render': '{project}/assets/{asset_type}/{asset_name}/render',
            'script': '{project}/scripts/{show}/{shot}/{task}',
            'output': '{project}/output/{show}/{shot}/{task}',
            'publish': '{project}/publish/{show}/{shot}/{task}/{version}'
        }
    
    def resolve_path(self, template_name: str, 
                    variables: Dict[str, str] = None) -> str:
        """
        Resolve a path using template and variables
        
        Args:
            template_name: Name of path template
            variables: Dictionary of variable values
            
        Returns:
            Resolved path
        """
        try:
            template = self.path_templates.get(template_name)
            if not template:
                raise ValueError(f"Unknown template: {template_name}")
            
            # Start with context variables
            context = self.env.get_project_config() or {}
            context_vars = {
                'project': self.env.get_env('PROJECT_ROOT'),
                'show': self.env.get_env('SHOW'),
                'shot': self.env.get_env('SHOT'),
                'task': self.env.get_env('TASK'),
                'dept': self.env.get_env('DEPT'),
                'user': self.env.get_user_info().get('username')
            }
            
            # Merge with provided variables
            all_vars = {**context_vars, **(variables or {})}
            
            # Apply variables to template
            path = template.format(**all_vars)
            
            # Expand environment variables
            path = os.path.expandvars(path)
            
            # Normalize path
            path = str(Path(path))
            
            return path
            
        except Exception as e:
            logger.error(f"Failed to resolve path {template_name}: {e}")
            return ""
    
    def ensure_path(self, template_name: str,
                   variables: Dict[str, str] = None) -> Tuple[bool, str]:
        """
        Ensure a path exists, create if necessary
        
        Args:
            template_name: Name of path template
            variables: Dictionary of variable values
            
        Returns:
            Tuple of (success, path)
        """
        try:
            path = self.resolve_path(template_name, variables)
            if not path:
                return False, ""
            
            # Create directory
            Path(path).mkdir(parents=True, exist_ok=True)
            
            return True, path
            
        except Exception as e:
            logger.error(f"Failed to ensure path {template_name}: {e}")
            return False, ""
    
    def get_shot_paths(self, show: str = None, 
                      shot: str = None) -> Dict[str, str]:
        """
        Get all paths for a shot
        
        Args:
            show: Show name
            shot: Shot name
            
        Returns:
            Dictionary of shot paths
        """
        try:
            if not show:
                show = self.env.get_env('SHOW')
            if not shot:
                shot = self.env.get_env('SHOT')
            
            if not show or not shot:
                return {}
            
            variables = {'show': show, 'shot': shot}
            paths = {}
            
            for template_name in self.path_templates.keys():
                if 'shot' in template_name or 'script' in template_name or 'output' in template_name:
                    path = self.resolve_path(template_name, variables)
                    if path:
                        paths[template_name] = path
            
            return paths
            
        except Exception as e:
            logger.error(f"Failed to get shot paths: {e}")
            return {}
    
    def get_asset_paths(self, asset_type: str,
                       asset_name: str) -> Dict[str, str]:
        """
        Get all paths for an asset
        
        Args:
            asset_type: Asset type (character, prop, environment, etc.)
            asset_name: Asset name
            
        Returns:
            Dictionary of asset paths
        """
        try:
            variables = {'asset_type': asset_type, 'asset_name': asset_name}
            paths = {}
            
            for template_name in self.path_templates.keys():
                if 'asset' in template_name:
                    path = self.resolve_path(template_name, variables)
                    if path:
                        paths[template_name] = path
            
            return paths
            
        except Exception as e:
            logger.error(f"Failed to get asset paths: {e}")
            return {}
    
    def find_latest_version(self, base_path: str,
                           pattern: str = "v{version:03d}") -> Optional[str]:
        """
        Find latest version in a directory
        
        Args:
            base_path: Base directory path
            pattern: Version pattern with {version} placeholder
            
        Returns:
            Latest version path or None
        """
        try:
            base_dir = Path(base_path)
            if not base_dir.exists():
                return None
            
            versions = []
            for item in base_dir.iterdir():
                if item.is_dir():
                    # Try to extract version from directory name
                    dir_name = item.name
                    
                    # Check if directory matches version pattern
                    version_match = re.search(r'v(\d+)', dir_name)
                    if version_match:
                        version_num = int(version_match.group(1))
                        versions.append((version_num, str(item)))
            
            if not versions:
                return None
            
            # Sort by version number
            versions.sort(key=lambda x: x[0])
            return versions[-1][1]
            
        except Exception as e:
            logger.error(f"Failed to find latest version: {e}")
            return None
    
    def create_version_path(self, base_path: str,
                          version: int = None,
                          pattern: str = "v{version:03d}") -> str:
        """
        Create a versioned path
        
        Args:
            base_path: Base directory path
            version: Version number (None for next version)
            pattern: Version pattern
            
        Returns:
            Versioned path
        """
        try:
            base_dir = Path(base_path)
            
            if version is None:
                # Find next version
                existing_versions = []
                for item in base_dir.iterdir():
                    if item.is_dir():
                        version_match = re.search(r'v(\d+)', item.name)
                        if version_match:
                            existing_versions.append(int(version_match.group(1)))
                
                version = max(existing_versions) + 1 if existing_versions else 1
            
            # Create version directory name
            version_dir = pattern.format(version=version)
            version_path = base_dir / version_dir
            
            # Create directory
            version_path.mkdir(parents=True, exist_ok=True)
            
            return str(version_path)
            
        except Exception as e:
            logger.error(f"Failed to create version path: {e}")
            return ""
    
    def validate_path_structure(self) -> Dict[str, Any]:
        """
        Validate project path structure
        
        Returns:
            Dictionary with validation results
        """
        try:
            results = {
                'valid': True,
                'missing_paths': [],
                'existing_paths': [],
                'errors': []
            }
            
            # Check required paths
            required_templates = ['shot_comp', 'shot_render', 'shot_plate']
            
            for template_name in required_templates:
                path = self.resolve_path(template_name)
                if path:
                    path_obj = Path(path)
                    if path_obj.exists():
                        results['existing_paths'].append({
                            'template': template_name,
                            'path': path,
                            'exists': True
                        })
                    else:
                        results['missing_paths'].append({
                            'template': template_name,
                            'path': path,
                            'exists': False
                        })
                        results['valid'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to validate path structure: {e}")
            return {'valid': False, 'errors': [str(e)]}
    
    def scan_directory(self, directory: str,
                      pattern: str = "*",
                      recursive: bool = False) -> List[str]:
        """
        Scan directory for files matching pattern
        
        Args:
            directory: Directory to scan
            pattern: File pattern
            recursive: Recursive scan
            
        Returns:
            List of file paths
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return []
            
            files = []
            if recursive:
                for file_path in dir_path.rglob(pattern):
                    if file_path.is_file():
                        files.append(str(file_path))
            else:
                for file_path in dir_path.glob(pattern):
                    if file_path.is_file():
                        files.append(str(file_path))
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Failed to scan directory: {e}")
            return []
    
    def get_relative_path(self, path: str, 
                         relative_to: str = None) -> str:
        """
        Get path relative to project or specified directory
        
        Args:
            path: Absolute path
            relative_to: Base directory (None for project root)
            
        Returns:
            Relative path
        """
        try:
            if relative_to is None:
                relative_to = self.env.get_env('PROJECT_ROOT')
            
            if not relative_to:
                return path
            
            path_obj = Path(path)
            base_obj = Path(relative_to)
            
            try:
                return str(path_obj.relative_to(base_obj))
            except ValueError:
                # Path is not under base directory
                return path
            
        except Exception as e:
            logger.error(f"Failed to get relative path: {e}")
            return path

# Helper functions
def resolve_path(template_name: str, **kwargs) -> str:
    """Helper function to resolve path"""
    paths = ProjectPaths()
    return paths.resolve_path(template_name, kwargs)

def ensure_path(template_name: str, **kwargs) -> Tuple[bool, str]:
    """Helper function to ensure path exists"""
    paths = ProjectPaths()
    return paths.ensure_path(template_name, kwargs)