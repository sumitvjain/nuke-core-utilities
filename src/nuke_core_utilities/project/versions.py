"""
Version management for projects and files
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import nuke

from ..core.logging_utils import get_loggeVersionManagerr, TimerContext
from ..core.env import get_env
from ..core.constants import *
from ..data.read_write import NukeFileHandler

logger = get_logger(__name__)




class VersionManager:
    """Version management for projects and files"""
    
    def __init__(self):
        self.env = get_env()
        self.file_handler = NukeFileHandler()
        self.version_file = ".versions.json"
    
    def get_current_version(self, filepath: str = None) -> Optional[int]:
        """
        Get current version of a file
        
        Args:
            filepath: File path (None for current script)
            
        Returns:
            Version number or None
        """
        try:
            if filepath is None:
                filepath = nuke.root().name()
            
            if not filepath:
                return None
            
            path = Path(filepath)
            stem = path.stem
            
            # Try to extract version from filename
            version_match = re.search(r'_v(\d+)$', stem)
            if version_match:
                return int(version_match.group(1))
            
            # Check for version in parent directory
            parent_dir = path.parent.name
            version_match = re.search(r'v(\d+)', parent_dir)
            if version_match:
                return int(version_match.group(1))
            
            return 1  # Default to version 1
            
        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return None
    
    def increment_version(self, filepath: str = None,
                         save_copy: bool = True) -> Tuple[Optional[int], Optional[str]]:
        """
        Increment version and optionally save copy
        
        Args:
            filepath: File path (None for current script)
            save_copy: Save a copy with new version
            
        Returns:
            Tuple of (new_version, new_filepath)
        """
        with TimerContext("increment_version", logger):
            try:
                if filepath is None:
                    filepath = nuke.root().name()
                
                if not filepath:
                    return None, None
                
                current_version = self.get_current_version(filepath) or 1
                new_version = current_version + 1
                
                # Create new filepath
                new_filepath = self._create_versioned_path(filepath, new_version)
                
                if save_copy:
                    # Save current script with new version
                    success = self.file_handler.write_nuke_script(
                        new_filepath,
                        overwrite=False,
                        backup=False
                    )
                    
                    if success:
                        # Update version metadata
                        self._update_version_metadata(new_filepath, new_version)
                        
                        logger.info(f"Incremented version to v{new_version:03d}: {new_filepath}")
                        return new_version, new_filepath
                    else:
                        return None, None
                else:
                    return new_version, new_filepath
                
            except Exception as e:
                logger.error(f"Failed to increment version: {e}")
                return None, None
    
    def get_version_history(self, filepath: str = None) -> List[Dict[str, Any]]:
        """
        Get version history for a file
        
        Args:
            filepath: Base file path
            
        Returns:
            List of version entries
        """
        try:
            if filepath is None:
                filepath = nuke.root().name()
            
            if not filepath:
                return []
            
            base_path = Path(filepath)
            base_dir = base_path.parent
            base_stem = base_path.stem
            
            # Remove version suffix from stem
            base_stem = re.sub(r'_v\d+$', '', base_stem)
            
            # Find all versions
            versions = []
            
            # Look for versioned files
            pattern = f"{base_stem}_v*.nk"
            for version_file in base_dir.glob(pattern):
                version_match = re.search(r'_v(\d+)', version_file.stem)
                if version_match:
                    version_num = int(version_match.group(1))
                    
                    # Get file info
                    try:
                        stat = version_file.stat()
                        versions.append({
                            'version': version_num,
                            'filepath': str(version_file),
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'current': version_file == base_path
                        })
                    except:
                        pass
            
            # Sort by version
            versions.sort(key=lambda x: x['version'])
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []
    
    def compare_versions(self, version1: int, version2: int,
                        base_path: str = None) -> Dict[str, Any]:
        """
        Compare two versions
        
        Args:
            version1: First version number
            version2: Second version number
            base_path: Base file path
            
        Returns:
            Comparison results
        """
        try:
            if base_path is None:
                base_path = nuke.root().name()
            
            if not base_path:
                return {}
            
            # Get file paths for both versions
            path1 = self._create_versioned_path(base_path, version1)
            path2 = self._create_versioned_path(base_path, version2)
            
            if not Path(path1).exists() or not Path(path2).exists():
                return {'error': 'Version files not found'}
            
            # Compare file sizes
            size1 = Path(path1).stat().st_size
            size2 = Path(path2).stat().st_size
            
            # Compare modification times
            mtime1 = datetime.fromtimestamp(Path(path1).stat().st_mtime)
            mtime2 = datetime.fromtimestamp(Path(path2).stat().st_mtime)
            
            # Load and compare scripts
            # Note: This is a simple comparison. For detailed node comparison,
            # you would need to load both scripts and compare node structures.
            
            return {
                'version1': version1,
                'version2': version2,
                'size_difference': size2 - size1,
                'time_difference': (mtime2 - mtime1).total_seconds(),
                'newer': version2 if mtime2 > mtime1 else version1
            }
            
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            return {}
    
    def restore_version(self, version: int,
                       base_path: str = None,
                       backup_current: bool = True) -> bool:
        """
        Restore a previous version
        
        Args:
            version: Version to restore
            base_path: Base file path
            backup_current: Backup current version before restoring
            
        Returns:
            Success status
        """
        try:
            if base_path is None:
                base_path = nuke.root().name()
            
            if not base_path:
                return False
            
            # Get path for version to restore
            restore_path = self._create_versioned_path(base_path, version)
            
            if not Path(restore_path).exists():
                logger.error(f"Version {version} not found: {restore_path}")
                return False
            
            # Backup current version if requested
            if backup_current and Path(base_path).exists():
                current_version = self.get_current_version(base_path) or 1
                backup_path = self._create_versioned_path(base_path, current_version)
                Path(base_path).rename(backup_path)
                logger.debug(f"Backed up current version to {backup_path}")
            
            # Copy restore version to current path
            import shutil
            shutil.copy2(restore_path, base_path)
            
            # Reload script
            nuke.scriptClear()
            nuke.scriptReadFile(base_path)
            
            logger.info(f"Restored version v{version:03d}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
            return False
    
    def cleanup_old_versions(self, base_path: str = None,
                           keep_versions: int = 10,
                           keep_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old versions
        
        Args:
            base_path: Base file path
            keep_versions: Number of recent versions to keep
            keep_days: Keep versions newer than this many days
            
        Returns:
            Cleanup results
        """
        try:
            if base_path is None:
                base_path = nuke.root().name()
            
            if not base_path:
                return {'deleted': 0, 'kept': 0, 'error': 'No base path'}
            
            # Get all versions
            versions = self.get_version_history(base_path)
            if not versions:
                return {'deleted': 0, 'kept': 0, 'message': 'No versions found'}
            
            # Sort by version (descending)
            versions.sort(key=lambda x: x['version'], reverse=True)
            
            current_time = datetime.now()
            deleted = []
            kept = []
            
            for i, version_info in enumerate(versions):
                version_path = Path(version_info['filepath'])
                version_time = datetime.fromisoformat(version_info['modified'])
                days_old = (current_time - version_time).days
                
                # Decision logic
                keep = False
                
                # Keep current version
                if version_info['current']:
                    keep = True
                
                # Keep recent versions
                elif i < keep_versions:
                    keep = True
                
                # Keep versions newer than keep_days
                elif days_old <= keep_days:
                    keep = True
                
                if keep:
                    kept.append(version_info['version'])
                else:
                    # Delete old version
                    try:
                        version_path.unlink()
                        deleted.append(version_info['version'])
                        logger.debug(f"Deleted old version v{version_info['version']:03d}")
                    except Exception as e:
                        logger.warning(f"Failed to delete version v{version_info['version']:03d}: {e}")
            
            result = {
                'deleted': len(deleted),
                'kept': len(kept),
                'deleted_versions': deleted,
                'kept_versions': kept
            }
            
            logger.info(f"Cleaned up versions: deleted {len(deleted)}, kept {len(kept)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup old versions: {e}")
            return {'deleted': 0, 'kept': 0, 'error': str(e)}
    
    def create_version_snapshot(self, filepath: str = None,
                               description: str = "",
                               tags: List[str] = None) -> bool:
        """
        Create a version snapshot with metadata
        
        Args:
            filepath: File path (None for current script)
            description: Snapshot description
            tags: List of tags
            
        Returns:
            Success status
        """
        try:
            if filepath is None:
                filepath = nuke.root().name()
            
            if not filepath:
                return False
            
            # Increment version
            new_version, new_filepath = self.increment_version(filepath, save_copy=True)
            
            if not new_version or not new_filepath:
                return False
            
            # Create snapshot metadata
            snapshot = {
                'version': new_version,
                'timestamp': datetime.now().isoformat(),
                'description': description,
                'tags': tags or [],
                'user': self.env.get_user_info().get('username'),
                'script_info': self._get_script_info()
            }
            
            # Save snapshot metadata
            snapshot_file = Path(new_filepath).with_suffix('.json')
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            
            logger.info(f"Created version snapshot v{new_version:03d}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create version snapshot: {e}")
            return False
    
    def _create_versioned_path(self, filepath: str, version: int) -> str:
        """Create versioned file path"""
        path = Path(filepath)
        stem = path.stem
        
        # Remove existing version suffix
        stem = re.sub(r'_v\d+$', '', stem)
        
        # Add new version suffix
        new_stem = f"{stem}_v{version:03d}"
        new_path = path.with_stem(new_stem)
        
        return str(new_path)
    
    def _update_version_metadata(self, filepath: str, version: int):
        """Update version metadata in file"""
        # This would require modifying the .nk file structure
        # For now, we'll just log it
        logger.debug(f"Updated version metadata for {filepath} to v{version:03d}")
    
    def _get_script_info(self) -> Dict[str, Any]:
        """Get script information for snapshot"""
        try:
            return {
                'node_count': len(nuke.allNodes()),
                'frame_range': (
                    nuke.root()['first_frame'].value(),
                    nuke.root()['last_frame'].value()
                ),
                'fps': nuke.root()['fps'].value(),
                'format': str(nuke.root()['format'].value())
            }
        except:
            return {}

# Helper functions
def get_current_version(filepath: str = None) -> Optional[int]:
    """Helper function to get current version"""
    manager = VersionManager()
    return manager.get_current_version(filepath)

def increment_version(filepath: str = None, **kwargs) -> Tuple[Optional[int], Optional[str]]:
    """Helper function to increment version"""
    manager = VersionManager()
    return manager.increment_version(filepath, **kwargs)

def get_version_history(filepath: str = None) -> List[Dict[str, Any]]:
    """Helper function to get version history"""
    manager = VersionManager()
    return manager.get_version_history(filepath)


def get_logger():
    pass