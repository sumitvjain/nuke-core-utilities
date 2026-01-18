"""
Metadata management for Nuke nodes and scripts
"""

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.constants import META_CREATOR, META_CREATED, META_MODIFIED, META_VERSION

logger = get_logger(__name__)

class MetadataManager:
    """Manager for Nuke metadata operations"""
    
    def __init__(self):
        self.metadata_cache = {}
        self.custom_knob_prefix = "metadata_"
    
    def extract_node_metadata(self, node: 'nuke.Node') -> Dict:
        """Extract metadata from a node"""
        metadata = {
            'basic': {
                'name': node.name(),
                'class': node.Class(),
                'position': (node.xpos(), node.ypos()),
                'color': node['tile_color'].value() if node.knob('tile_color') else 0,
                'disabled': node['disable'].value() if node.knob('disable') else False,
            },
            'knobs': {},
            'connections': {},
            'custom': {}
        }
        
        # Extract knob values
        for knob_name in node.knobs():
            knob = node[knob_name]
            if knob and knob.visible():
                try:
                    metadata['knobs'][knob_name] = {
                        'value': knob.value(),
                        'type': knob.Class(),
                        'label': knob.label(),
                        'is_animated': self._is_knob_animated(knob)
                    }
                except:
                    pass
        
        # Extract input connections
        inputs = {}
        for i in range(node.inputs()):
            input_node = node.input(i)
            if input_node:
                inputs[f'input{i}'] = input_node.name()
        metadata['connections']['inputs'] = inputs
        
        # Extract custom metadata from knobs
        metadata['custom'] = self._extract_custom_metadata(node)
        
        return metadata
    
    def _is_knob_animated(self, knob: 'nuke.Knob') -> bool:
        """Check if a knob is animated"""
        try:
            if knob.hasExpression() or knob.isAnimated():
                return True
            
            # Check for keyframes
            anim_curve = knob.animation(0)
            if anim_curve and anim_curve.keys():
                return True
        except:
            pass
        return False
    
    def _extract_custom_metadata(self, node: 'nuke.Node') -> Dict:
        """Extract custom metadata from knobs"""
        custom_data = {}
        
        # Look for metadata knobs
        for knob_name in node.knobs():
            if knob_name.startswith(self.custom_knob_prefix):
                knob = node[knob_name]
                if knob:
                    try:
                        key = knob_name[len(self.custom_knob_prefix):]
                        custom_data[key] = knob.value()
                    except:
                        pass
        
        # Check for metadata in label or other fields
        label_knob = node.knob('label')
        if label_knob:
            label = label_knob.value()
            if label:
                # Try to parse JSON from label
                if label.startswith('{') and label.endswith('}'):
                    try:
                        label_data = json.loads(label)
                        custom_data.update(label_data)
                    except:
                        pass
        
        return custom_data
    
    def set_node_metadata(self, node: 'nuke.Node', key: str, value: Any,
                         knob_type: str = 'String_Knob'):
        """Set metadata on a node"""
        knob_name = f"{self.custom_knob_prefix}{key}"
        
        # Check if knob exists
        existing_knob = node.knob(knob_name)
        if existing_knob:
            try:
                existing_knob.setValue(str(value))
                return True
            except Exception as e:
                logger.error(f"Failed to set metadata knob value: {e}")
                return False
        
        # Create new knob
        try:
            if knob_type == 'String_Knob':
                knob = nuke.String_Knob(knob_name, key.replace('_', ' ').title())
                knob.setValue(str(value))
            elif knob_type == 'Text_Knob':
                knob = nuke.Text_Knob(knob_name, key.replace('_', ' ').title())
                knob.setValue(str(value))
            elif knob_type == 'Boolean_Knob':
                knob = nuke.Boolean_Knob(knob_name, key.replace('_', ' ').title())
                knob.setValue(bool(value))
            elif knob_type == 'Int_Knob':
                knob = nuke.Int_Knob(knob_name, key.replace('_', ' ').title())
                knob.setValue(int(value))
            elif knob_type == 'Float_Knob':
                knob = nuke.Float_Knob(knob_name, key.replace('_', ' ').title())
                knob.setValue(float(value))
            else:
                logger.error(f"Unsupported knob type: {knob_type}")
                return False
            
            # Add to node
            node.addKnob(knob)
            
            # Move to end of knob list
            try:
                tab_knob = node.knob('Node')
                if tab_knob:
                    node.removeKnob(knob)
                    node.addKnob(knob)
                    node.setInput(0, None)  # Workaround to refresh UI
            except:
                pass
            
            logger.debug(f"Added metadata knob '{knob_name}' to node '{node.name()}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create metadata knob: {e}")
            return False
    
    def get_node_metadata(self, node: 'nuke.Node', key: str = None, 
                         default: Any = None) -> Any:
        """Get metadata from a node"""
        if key is None:
            return self._extract_custom_metadata(node)
        
        knob_name = f"{self.custom_knob_prefix}{key}"
        knob = node.knob(knob_name)
        
        if knob:
            try:
                return knob.value()
            except:
                return default
        
        return default
    
    def remove_node_metadata(self, node: 'nuke.Node', key: str) -> bool:
        """Remove metadata from a node"""
        knob_name = f"{self.custom_knob_prefix}{key}"
        knob = node.knob(knob_name)
        
        if knob:
            try:
                node.removeKnob(knob)
                logger.debug(f"Removed metadata knob '{knob_name}' from node '{node.name()}'")
                return True
            except Exception as e:
                logger.error(f"Failed to remove metadata knob: {e}")
                return False
        
        return False
    
    def extract_script_metadata(self) -> Dict:
        """Extract metadata from entire script"""
        metadata = {
            'script_info': self._get_script_info(),
            'nodes': {},
            'statistics': self._get_script_statistics(),
            'versions': self._get_version_info(),
            'user_data': self._get_user_info()
        }
        
        # Extract metadata from all nodes
        for node in nuke.allNodes():
            try:
                node_meta = self.extract_node_metadata(node)
                metadata['nodes'][node.name()] = node_meta
            except Exception as e:
                logger.error(f"Failed to extract metadata from node {node.name()}: {e}")
        
        return metadata
    
    def _get_script_info(self) -> Dict:
        """Get script information"""
        try:
            root = nuke.root()
            return {
                'filename': root.name(),
                'fps': root['fps'].value(),
                'frame_range': (root['first_frame'].value(), root['last_frame'].value()),
                'format': str(root['format'].value()),
                'project_directory': nuke.getFileNameDirectory(root.name()),
                'modified': self._get_file_modified_time(root.name())
            }
        except:
            return {}
    
    def _get_file_modified_time(self, filepath: str) -> Optional[str]:
        """Get file modification time"""
        try:
            if filepath and Path(filepath).exists():
                mtime = Path(filepath).stat().st_mtime
                return datetime.fromtimestamp(mtime).isoformat()
        except:
            pass
        return None
    
    def _get_script_statistics(self) -> Dict:
        """Get script statistics"""
        try:
            nodes = nuke.allNodes()
            return {
                'total_nodes': len(nodes),
                'node_types': self._count_node_types(nodes),
                'backdrops': len([n for n in nodes if n.Class() == 'BackdropNode']),
                'read_nodes': len([n for n in nodes if n.Class() == 'Read']),
            }
        except:
            pass
        return None