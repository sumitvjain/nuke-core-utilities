"""
Write node management and utilities
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.env import get_env
from ..core.constants import *
from ..project.paths import ProjectPaths

logger = get_logger(__name__)

class WriteNodeManager:
    """Write node management and utilities"""
    
    def __init__(self):
        self.env = get_env()
        self.paths = ProjectPaths()
        self.write_node_templates = self._load_write_templates()
    
    def _load_write_templates(self) -> Dict[str, Any]:
        """Load write node templates"""
        return {
            'exr_16bit': {
                'file_type': 'exr',
                'channels': 'rgba',
                'compression': 'zip',
                'bit_depth': 16,
                'colorspace': 'linear'
            },
            'exr_32bit': {
                'file_type': 'exr',
                'channels': 'rgba',
                'compression': 'zip',
                'bit_depth': 32,
                'colorspace': 'linear'
            },
            'jpeg': {
                'file_type': 'jpeg',
                'quality': 0.95,
                'colorspace': 'sRGB'
            },
            'png_16bit': {
                'file_type': 'png',
                'channels': 'rgba',
                'bit_depth': 16
            },
            'mov_prores': {
                'file_type': 'mov',
                'codec': 'ap4h',
                'quality': 3,
                'colorspace': 'sRGB'
            }
        }
    
    def create_write_node(self, template: str = 'exr_16bit',
                         name: str = None,
                         filepath: str = None,
                         position: Tuple[int, int] = None) -> Optional['nuke.Node']:
        """
        Create a write node from template
        
        Args:
            template: Template name
            name: Node name
            filepath: Output file path
            position: Node position
            
        Returns:
            Created write node or None
        """
        with TimerContext(f"create_write_node_{template}", logger):
            try:
                # Get template
                template_config = self.write_node_templates.get(template)
                if not template_config:
                    logger.error(f"Unknown write template: {template}")
                    return None
                
                # Create write node
                write_node = nuke.createNode('Write')
                
                # Set name
                if name:
                    write_node.setName(name)
                else:
                    # Generate name from template
                    write_node.setName(f"Write_{template}")
                
                # Set position
                if position:
                    write_node.setXpos(position[0])
                    write_node.setYpos(position[1])
                
                # Configure from template
                self._configure_write_node(write_node, template_config)
                
                # Set filepath if provided
                if filepath:
                    self.set_write_filepath(write_node, filepath)
                
                logger.info(f"Created write node '{write_node.name()}' from template '{template}'")
                return write_node
                
            except Exception as e:
                logger.error(f"Failed to create write node: {e}")
                return None
    
    def _configure_write_node(self, node: 'nuke.Node', config: Dict[str, Any]):
        """Configure write node from template"""
        try:
            # Set file type
            if 'file_type' in config:
                file_knob = node.knob('file_type')
                if file_knob:
                    file_knob.setValue(config['file_type'])
            
            # Set channels
            if 'channels' in config:
                channels_knob = node.knob('channels')
                if channels_knob:
                    channels_knob.setValue(config['channels'])
            
            # Set compression
            if 'compression' in config:
                comp_knob = node.knob('compression')
                if comp_knob:
                    comp_knob.setValue(config['compression'])
            
            # Set bit depth
            if 'bit_depth' in config:
                datatype_knob = node.knob('datatype')
                if datatype_knob:
                    if config['bit_depth'] == 8:
                        datatype_knob.setValue('8 bit')
                    elif config['bit_depth'] == 16:
                        datatype_knob.setValue('16 bit')
                    elif config['bit_depth'] == 32:
                        datatype_knob.setValue('32 bit')
            
            # Set colorspace
            if 'colorspace' in config:
                colorspace_knob = node.knob('colorspace')
                if colorspace_knob:
                    colorspace_knob.setValue(config['colorspace'])
            
            # Set quality for JPEG/MOV
            if 'quality' in config:
                quality_knob = node.knob('quality')
                if quality_knob:
                    quality_knob.setValue(config['quality'])
            
            # Set codec for MOV
            if 'codec' in config:
                codec_knob = node.knob('codec')
                if codec_knob:
                    codec_knob.setValue(config['codec'])
                    
        except Exception as e:
            logger.warning(f"Failed to configure write node: {e}")
    
    def set_write_filepath(self, node: 'nuke.Node',
                          filepath: str,
                          frame_padding: int = 4) -> bool:
        """
        Set write node filepath with frame padding
        
        Args:
            node: Write node
            filepath: Output file path
            frame_padding: Frame number padding
            
        Returns:
            Success status
        """
        try:
            file_knob = node.knob('file')
            if not file_knob:
                return False
            
            # Ensure directory exists
            path_obj = Path(filepath)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Add frame padding if needed
            if '%' not in filepath and '#' not in filepath:
                # Add frame padding
                stem = path_obj.stem
                suffix = path_obj.suffix
                parent = path_obj.parent
                
                # Create sequence pattern
                frame_pattern = f"%0{frame_padding}d"
                new_filename = f"{stem}.{frame_pattern}{suffix}"
                new_filepath = parent / new_filename
            
                file_knob.setValue(str(new_filepath))
            else:
                file_knob.setValue(filepath)
            
            logger.debug(f"Set write node filepath: {node.name()} -> {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set write filepath: {e}")
            return False
    
    def auto_configure_write_node(self, node: 'nuke.Node',
                                 template: str = None) -> bool:
        """
        Auto-configure write node based on context
        
        Args:
            node: Write node
            template: Template name (None for auto-detect)
            
        Returns:
            Success status
        """
        try:
            if not template:
                # Auto-detect based on node name or file extension
                file_knob = node.knob('file')
                if file_knob:
                    filepath = file_knob.value()
                    if filepath:
                        # Get file extension
                        ext = Path(filepath).suffix.lower()
                        
                        if ext == '.exr':
                            template = 'exr_16bit'
                        elif ext == '.jpg' or ext == '.jpeg':
                            template = 'jpeg'
                        elif ext == '.png':
                            template = 'png_16bit'
                        elif ext == '.mov':
                            template = 'mov_prores'
            
            if template:
                config = self.write_node_templates.get(template)
                if config:
                    self._configure_write_node(node, config)
                    logger.debug(f"Auto-configured write node '{node.name()}' with template '{template}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to auto-configure write node: {e}")
            return False
    
    def get_write_node_info(self, node: 'nuke.Node') -> Dict[str, Any]:
        """
        Get information about a write node
        
        Args:
            node: Write node
            
        Returns:
            Write node information
        """
        try:
            info = {
                'name': node.name(),
                'filepath': node.knob('file').value() if node.knob('file') else '',
                'file_type': node.knob('file_type').value() if node.knob('file_type') else '',
                'channels': node.knob('channels').value() if node.knob('channels') else '',
                'frame_range': self._get_write_frame_range(node),
                'estimated_size': self._estimate_write_size(node),
                'status': self._get_write_status(node)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get write node info: {e}")
            return {}
    
    def _get_write_frame_range(self, node: 'nuke.Node') -> Tuple[int, int]:
        """Get frame range for write node"""
        try:
            first_frame = nuke.root()['first_frame'].value()
            last_frame = nuke.root()['last_frame'].value()
            
            # Check for frame range knob
            frame_range_knob = node.knob('frame_range')
            if frame_range_knob:
                range_value = frame_range_knob.value()
                if range_value == 'all':
                    return (first_frame, last_frame)
                elif range_value == 'intersection':
                    # Would need to calculate based on inputs
                    pass
            
            return (first_frame, last_frame)
            
        except:
            return (1, 100)
    
    def _estimate_write_size(self, node: 'nuke.Node') -> Dict[str, Any]:
        """Estimate output file size"""
        try:
            # Get frame range
            first_frame, last_frame = self._get_write_frame_range(node)
            frame_count = last_frame - first_frame + 1
            
            # Get format
            root_format = nuke.root()['format'].value()
            width = root_format.width()
            height = root_format.height()
            pixels = width * height
            
            # Get file type and bit depth
            file_type = node.knob('file_type').value() if node.knob('file_type') else 'exr'
            channels = node.knob('channels').value() if node.knob('channels') else 'rgba'
            
            # Calculate bytes per pixel
            if file_type == 'exr':
                # EXR: typically 16 bytes per pixel for RGBA half float
                bytes_per_pixel = 16
            elif file_type == 'png':
                # PNG: 4 bytes per pixel for RGBA 8-bit
                bytes_per_pixel = 4
            elif file_type == 'jpeg':
                # JPEG: compressed, estimate 1 byte per pixel
                bytes_per_pixel = 1
            else:
                bytes_per_pixel = 4  # Default
            
            # Calculate total size
            total_bytes = pixels * bytes_per_pixel * frame_count
            total_gb = total_bytes / (1024**3)
            
            return {
                'frames': frame_count,
                'resolution': f"{width}x{height}",
                'pixels': pixels,
                'bytes_per_frame': pixels * bytes_per_pixel,
                'total_bytes': total_bytes,
                'total_gb': total_gb,
                'estimated': True
            }
            
        except Exception as e:
            logger.warning(f"Failed to estimate write size: {e}")
            return {'error': str(e)}
    
    def _get_write_status(self, node: 'nuke.Node') -> str:
        """Get write node status"""
        try:
            # Check if disabled
            disable_knob = node.knob('disable')
            if disable_knob and disable_knob.value():
                return 'disabled'
            
            # Check filepath
            file_knob = node.knob('file')
            if not file_knob or not file_knob.value():
                return 'no_filepath'
            
            # Check if file exists
            filepath = file_knob.value()
            if '%' in filepath or '#' in filepath:
                # Sequence - check if any frames exist
                import glob
                pattern = re.sub(r'%0\d+d', '*', filepath)
                pattern = re.sub(r'#+', '*', pattern)
                existing = glob.glob(pattern)
                if existing:
                    return 'partial'
                else:
                    return 'ready'
            else:
                # Single file
                if Path(filepath).exists():
                    return 'exists'
                else:
                    return 'ready'
                    
        except:
            return 'unknown'
    
    def validate_write_nodes(self, nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
        """
        Validate write nodes
        
        Args:
            nodes: Write nodes to validate (None for all write nodes)
            
        Returns:
            Validation results
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes('Write')
            
            results = {
                'total': len(nodes),
                'valid': [],
                'warnings': [],
                'errors': []
            }
            
            for node in nodes:
                validation = self._validate_write_node(node)
                
                if validation['valid']:
                    results['valid'].append({
                        'node': node.name(),
                        'info': validation
                    })
                elif validation.get('error'):
                    results['errors'].append({
                        'node': node.name(),
                        'error': validation['error']
                    })
                elif validation.get('warning'):
                    results['warnings'].append({
                        'node': node.name(),
                        'warning': validation['warning']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to validate write nodes: {e}")
            return {'error': str(e)}
    
    def _validate_write_node(self, node: 'nuke.Node') -> Dict[str, Any]:
        """Validate a single write node"""
        try:
            validation = {'valid': True}
            
            # Check filepath
            file_knob = node.knob('file')
            if not file_knob or not file_knob.value():
                validation['valid'] = False
                validation['error'] = 'No filepath specified'
                return validation
            
            filepath = file_knob.value()
            
            # Check directory permissions
            try:
                path_obj = Path(filepath)
                # Clean path for sequence patterns
                clean_path = re.sub(r'%0\d+d', '0001', filepath)
                clean_path = re.sub(r'#+', '0001', clean_path)
                path_obj = Path(clean_path)
                
                # Check parent directory
                parent = path_obj.parent
                if not parent.exists():
                    validation['warning'] = f'Directory does not exist: {parent}'
                else:
                    # Check write permissions
                    test_file = parent / '.write_test'
                    try:
                        test_file.touch()
                        test_file.unlink()
                    except PermissionError:
                        validation['error'] = f'No write permission in directory: {parent}'
                        validation['valid'] = False
            except Exception as e:
                validation['warning'] = f'Could not validate directory: {e}'
            
            # Check disk space
            if validation['valid']:
                size_estimate = self._estimate_write_size(node)
                if 'total_gb' in size_estimate:
                    required_gb = size_estimate['total_gb']
                    if required_gb > 1:  # Only check for large files
                        import shutil
                        temp_dir = self.env.get_nuke_temp_dir()
                        total, used, free = shutil.disk_usage(temp_dir)
                        free_gb = free / (1024**3)
                        
                        if free_gb < required_gb * 1.5:  # Need 50% extra space
                            validation['warning'] = f'Low disk space: {free_gb:.1f}GB free, {required_gb:.1f}GB estimated'
            
            return validation
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}

# Helper functions
def create_write_node(template: str = 'exr_16bit', **kwargs) -> Optional['nuke.Node']:
    """Helper function to create write node"""
    manager = WriteNodeManager()
    return manager.create_write_node(template, **kwargs)

def validate_write_nodes(nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
    """Helper function to validate write nodes"""
    manager = WriteNodeManager()
    return manager.validate_write_nodes(nodes)