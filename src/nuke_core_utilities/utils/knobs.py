"""
Knob management and utilities
"""

import json
from typing import Dict, List, Optional, Any, Union, Tuple
import nuke

from ..core.logging_utils import get_logger
from ..core.constants import *

logger = get_logger(__name__)

class KnobManager:
    """Knob management and utilities"""
    
    def __init__(self):
        self.knob_types = {
            'string': nuke.String_Knob,
            'text': nuke.Text_Knob,
            'int': nuke.Int_Knob,
            'float': nuke.Float_Knob,
            'bool': nuke.Boolean_Knob,
            'color': nuke.Color_Knob,
            'file': nuke.File_Knob,
            'enum': nuke.Enumeration_Knob,
            'py': nuke.PyScript_Knob,
            'tab': nuke.Tab_Knob,
            'xy': nuke.XY_Knob
        }
    
    def get_knob_info(self, node: 'nuke.Node', knob_name: str) -> Dict[str, Any]:
        """
        Get information about a knob
        
        Args:
            node: Node containing the knob
            knob_name: Knob name
            
        Returns:
            Knob information
        """
        try:
            knob = node.knob(knob_name)
            if not knob:
                return {}
            
            info = {
                'name': knob_name,
                'type': knob.Class(),
                'value': knob.value(),
                'label': knob.label(),
                'visible': knob.visible(),
                'enabled': knob.enabled(),
                'is_animated': self._is_knob_animated(knob),
                'has_expression': knob.hasExpression(),
                'default_value': self._get_knob_default_value(knob),
                'min_max': self._get_knob_min_max(knob)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get knob info: {e}")
            return {}
    
    def set_knob_value(self, node: 'nuke.Node', knob_name: str, 
                      value: Any, animated: bool = False) -> bool:
        """
        Set knob value
        
        Args:
            node: Node containing the knob
            knob_name: Knob name
            value: Value to set
            animated: Set as animated value
            
        Returns:
            Success status
        """
        try:
            knob = node.knob(knob_name)
            if not knob:
                return False
            
            if animated:
                # Set animated value
                knob.setAnimated()
                knob.setValueAt(value, nuke.frame())
            else:
                knob.setValue(value)
            
            logger.debug(f"Set knob {node.name()}.{knob_name} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set knob value: {e}")
            return False
    
    def create_knob(self, node: 'nuke.Node', knob_type: str,
                   name: str, label: str = None,
                   default_value: Any = None,
                   flags: int = 0) -> Optional['nuke.Knob']:
        """
        Create and add a knob to a node
        
        Args:
            node: Node to add knob to
            knob_type: Knob type (string, int, float, bool, etc.)
            name: Knob name
            label: Knob label (defaults to name)
            default_value: Default value
            flags: Knob flags
            
        Returns:
            Created knob or None
        """
        try:
            knob_class = self.knob_types.get(knob_type.lower())
            if not knob_class:
                logger.error(f"Unknown knob type: {knob_type}")
                return None
            
            if label is None:
                label = name.replace('_', ' ').title()
            
            # Create knob
            knob = knob_class(name, label)
            
            # Set default value if provided
            if default_value is not None:
                try:
                    knob.setValue(default_value)
                except:
                    pass
            
            # Set flags
            if flags:
                knob.setFlag(flags)
            
            # Add to node
            node.addKnob(knob)
            
            logger.debug(f"Created knob {knob_type} '{name}' on node '{node.name()}'")
            return knob
            
        except Exception as e:
            logger.error(f"Failed to create knob: {e}")
            return None
    
    def copy_knobs(self, source_node: 'nuke.Node', target_node: 'nuke.Node',
                  knob_names: List[str] = None,
                  copy_values: bool = True,
                  copy_animations: bool = True) -> Dict[str, bool]:
        """
        Copy knobs from one node to another
        
        Args:
            source_node: Source node
            target_node: Target node
            knob_names: List of knob names to copy (None for all)
            copy_values: Copy knob values
            copy_animations: Copy animations
            
        Returns:
            Dictionary mapping knob names to success status
        """
        try:
            results = {}
            
            # Determine which knobs to copy
            if knob_names is None:
                knob_names = source_node.knobs().keys()
            
            for knob_name in knob_names:
                try:
                    source_knob = source_node.knob(knob_name)
                    if not source_knob:
                        results[knob_name] = False
                        continue
                    
                    # Check if target has knob
                    target_knob = target_node.knob(knob_name)
                    if not target_knob:
                        # Create knob on target
                        knob_type = source_knob.Class()
                        self.create_knob(target_node, knob_type, knob_name)
                        target_knob = target_node.knob(knob_name)
                    
                    if copy_values:
                        if copy_animations and source_knob.isAnimated():
                            # Copy animation curves
                            self._copy_animation(source_knob, target_knob)
                        else:
                            # Copy static value
                            target_knob.setValue(source_knob.value())
                    
                    results[knob_name] = True
                    
                except Exception as e:
                    logger.debug(f"Failed to copy knob {knob_name}: {e}")
                    results[knob_name] = False
            
            logger.debug(f"Copied {sum(results.values())}/{len(results)} knobs")
            return results
            
        except Exception as e:
            logger.error(f"Failed to copy knobs: {e}")
            return {}
    
    def _copy_animation(self, source_knob: 'nuke.Knob', target_knob: 'nuke.Knob'):
        """Copy animation from one knob to another"""
        try:
            # Clear existing animation
            if target_knob.isAnimated():
                target_knob.clearAnimated()
            
            # Copy keyframes
            for dimension in range(source_knob.arraySize()):
                anim_curve = source_knob.animation(dimension)
                if anim_curve and anim_curve.keys():
                    target_knob.setAnimated(dimension)
                    target_anim = target_knob.animation(dimension)
                    
                    for key in anim_curve.keys():
                        target_anim.addKey(key.x, key.y, key.l, key.r, key.i)
        except:
            pass
    
    def get_knob_default_value(self, node: 'nuke.Node', knob_name: str) -> Any:
        """
        Get default value for a knob
        
        Args:
            node: Node containing the knob
            knob_name: Knob name
            
        Returns:
            Default value
        """
        try:
            # This is a simplified implementation
            # In practice, getting true defaults requires creating a new node
            knob = node.knob(knob_name)
            if not knob:
                return None
            
            knob_type = knob.Class()
            
            # Common defaults
            if knob_type == 'Boolean_Knob':
                return False
            elif knob_type == 'Int_Knob':
                return 0
            elif knob_type == 'Float_Knob':
                return 0.0
            elif knob_type == 'String_Knob':
                return ''
            elif knob_type == 'Color_Knob':
                return 0
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get knob default: {e}")
            return None
    
    def reset_knob_to_default(self, node: 'nuke.Node', knob_name: str) -> bool:
        """
        Reset knob to default value
        
        Args:
            node: Node containing the knob
            knob_name: Knob name
            
        Returns:
            Success status
        """
        try:
            knob = node.knob(knob_name)
            if not knob:
                return False
            
            default_value = self.get_knob_default_value(node, knob_name)
            if default_value is not None:
                knob.setValue(default_value)
                
                # Clear animation if present
                if knob.isAnimated():
                    knob.clearAnimated()
                
                logger.debug(f"Reset knob {node.name()}.{knob_name} to default")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to reset knob: {e}")
            return False
    
    def create_knob_group(self, node: 'nuke.Node', group_name: str,
                         knob_names: List[str],
                         label: str = None) -> bool:
        """
        Create a tab group for knobs
        
        Args:
            node: Node to add group to
            group_name: Group name
            knob_names: List of knob names to include
            label: Group label
            
        Returns:
            Success status
        """
        try:
            if label is None:
                label = group_name.replace('_', ' ').title()
            
            # Create tab knob
            tab_knob = nuke.Tab_Knob(group_name, label)
            node.addKnob(tab_knob)
            
            # Move specified knobs to this tab
            for knob_name in knob_names:
                knob = node.knob(knob_name)
                if knob:
                    # Remove and re-add to move to end (after tab)
                    node.removeKnob(knob)
                    node.addKnob(knob)
            
            logger.debug(f"Created knob group '{group_name}' on node '{node.name()}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create knob group: {e}")
            return False
    
    def export_knob_preset(self, node: 'nuke.Node',
                          knob_names: List[str] = None,
                          filepath: str = None) -> bool:
        """
        Export knob values as preset
        
        Args:
            node: Node to export from
            knob_names: List of knob names to export (None for all)
            filepath: Output file path
            
        Returns:
            Success status
        """
        try:
            if knob_names is None:
                knob_names = node.knobs().keys()
            
            preset = {
                'node_class': node.Class(),
                'node_name': node.name(),
                'knobs': {}
            }
            
            for knob_name in knob_names:
                knob = node.knob(knob_name)
                if knob:
                    try:
                        knob_info = self.get_knob_info(node, knob_name)
                        preset['knobs'][knob_name] = knob_info
                    except:
                        pass
            
            if filepath is None:
                # Create default filepath
                import tempfile
                filepath = f"{tempfile.gettempdir()}/{node.name()}_preset.json"
            
            with open(filepath, 'w') as f:
                json.dump(preset, f, indent=2)
            
            logger.info(f"Exported knob preset for {node.name()} to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export knob preset: {e}")
            return False
    
    def import_knob_preset(self, node: 'nuke.Node', filepath: str) -> bool:
        """
        Import knob values from preset
        
        Args:
            node: Node to import to
            filepath: Preset file path
            
        Returns:
            Success status
        """
        try:
            with open(filepath, 'r') as f:
                preset = json.load(f)
            
            if preset.get('node_class') != node.Class():
                logger.warning(f"Preset node class {preset.get('node_class')} doesn't match {node.Class()}")
            
            knobs_imported = 0
            for knob_name, knob_info in preset.get('knobs', {}).items():
                knob = node.knob(knob_name)
                if knob:
                    try:
                        value = knob_info.get('value')
                        if value is not None:
                            knob.setValue(value)
                            knobs_imported += 1
                    except:
                        pass
            
            logger.info(f"Imported {knobs_imported} knobs from preset {filepath}")
            return knobs_imported > 0
            
        except Exception as e:
            logger.error(f"Failed to import knob preset: {e}")
            return False
    
    def _is_knob_animated(self, knob: 'nuke.Knob') -> bool:
        """Check if knob is animated"""
        try:
            return knob.isAnimated() or knob.hasExpression()
        except:
            return False
    
    def _get_knob_default_value(self, knob: 'nuke.Knob') -> Any:
        """Get knob default value"""
        try:
            # This is a simplified approach
            knob_type = knob.Class()
            
            if knob_type == 'Boolean_Knob':
                return False
            elif knob_type == 'Int_Knob':
                return 0
            elif knob_type == 'Float_Knob':
                return 0.0
            elif knob_type == 'String_Knob':
                return ''
            elif knob_type == 'Color_Knob':
                return 0
            else:
                return None
        except:
            return None
    
    def _get_knob_min_max(self, knob: 'nuke.Knob') -> Optional[Tuple[float, float]]:
        """Get knob minimum and maximum values"""
        try:
            knob_type = knob.Class()
            
            if knob_type == 'Int_Knob':
                return (knob.minimum(), knob.maximum())
            elif knob_type == 'Float_Knob':
                return (knob.minimum(), knob.maximum())
            else:
                return None
        except:
            return None

# Helper functions
def get_knob_info(node: 'nuke.Node', knob_name: str) -> Dict[str, Any]:
    """Helper function to get knob info"""
    manager = KnobManager()
    return manager.get_knob_info(node, knob_name)

def set_knob_value(node: 'nuke.Node', knob_name: str, value: Any, **kwargs) -> bool:
    """Helper function to set knob value"""
    manager = KnobManager()
    return manager.set_knob_value(node, knob_name, value, **kwargs)

def copy_knobs(source: 'nuke.Node', target: 'nuke.Node', **kwargs) -> Dict[str, bool]:
    """Helper function to copy knobs"""
    manager = KnobManager()
    return manager.copy_knobs(source, target, **kwargs)