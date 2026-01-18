"""
Node modification and transformation utilities
"""

import math
from typing import Dict, List, Tuple, Optional, Any, Union
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.constants import *
from ..data.cache import cached_function

logger = get_logger(__name__)

class NodeModifier:
    """Node modification and transformation utilities"""
    
    def __init__(self):
        self.default_colors = {
            'transform': COLOR_TRANSFORM,
            'effect': COLOR_EFFECT,
            'input': COLOR_INPUT,
            'output': COLOR_OUTPUT,
            '3d': COLOR_3D,
            'utility': COLOR_UTILITY,
            'group': COLOR_GROUP
        }
    
    def set_node_color(self, node: 'nuke.Node', 
                      color: Union[int, str]) -> bool:
        """
        Set node tile color
        
        Args:
            node: Node to modify
            color: Color as integer or color name
            
        Returns:
            Success status
        """
        try:
            if isinstance(color, str):
                # Get color from name
                color = getattr(COLOR, color.upper(), COLOR_UTILITY)
            
            tile_color_knob = node.knob('tile_color')
            if tile_color_knob:
                tile_color_knob.setValue(color)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to set node color: {e}")
            return False
    
    def color_nodes_by_type(self, nodes: List['nuke.Node'] = None) -> Dict[str, int]:
        """
        Color nodes by their type/function
        
        Args:
            nodes: Nodes to color (None for all nodes)
            
        Returns:
            Dictionary mapping node classes to color counts
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes()
            
            color_counts = defaultdict(int)
            
            for node in nodes:
                node_class = node.Class()
                color = self._get_color_for_node_class(node_class)
                
                if self.set_node_color(node, color):
                    color_counts[node_class] += 1
            
            logger.info(f"Colored {len(nodes)} nodes by type")
            return dict(color_counts)
            
        except Exception as e:
            logger.error(f"Failed to color nodes by type: {e}")
            return {}
    
    def rename_nodes(self, nodes: List['nuke.Node'] = None,
                    pattern: str = "{class}_{index:03d}",
                    start_index: int = 1,
                    dry_run: bool = False) -> Dict[str, str]:
        """
        Rename nodes with pattern
        
        Args:
            nodes: Nodes to rename (None for selected nodes)
            pattern: Naming pattern with {class}, {index}, {old_name} placeholders
            start_index: Starting index
            dry_run: Only show what would be renamed
            
        Returns:
            Dictionary mapping old names to new names
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                return {}
            
            rename_map = {}
            index = start_index
            
            for node in nodes:
                old_name = node.name()
                node_class = node.Class().lower()
                
                # Generate new name
                new_name = pattern.format(
                    node_class,
                    index=index,
                    old_name=old_name
                )
                
                # Ensure unique name
                new_name = self._ensure_unique_name(new_name, node)
                
                if not dry_run:
                    node.setName(new_name)
                
                rename_map[old_name] = new_name
                index += 1
            
            if not dry_run:
                logger.info(f"Renamed {len(nodes)} nodes")
            else:
                logger.info(f"Dry run: Would rename {len(nodes)} nodes")
            
            return rename_map
            
        except Exception as e:
            logger.error(f"Failed to rename nodes: {e}")
            return {}
    
    def align_nodes(self, nodes: List['nuke.Node'] = None,
                   alignment: str = 'left',
                   spacing: int = 20) -> bool:
        """
        Align nodes horizontally or vertically
        
        Args:
            nodes: Nodes to align (None for selected nodes)
            alignment: 'left', 'right', 'top', 'bottom', 'horizontal', 'vertical'
            spacing: Spacing between nodes
            
        Returns:
            Success status
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if len(nodes) < 2:
                return False
            
            if alignment in ['left', 'right', 'horizontal']:
                # Sort by y position
                nodes.sort(key=lambda n: n.ypos())
                
                # Align
                if alignment == 'left':
                    x_pos = min(n.xpos() for n in nodes)
                    for node in nodes:
                        node.setXpos(x_pos)
                elif alignment == 'right':
                    x_pos = max(n.xpos() + n.screenWidth() for n in nodes)
                    for node in nodes:
                        node.setXpos(x_pos - node.screenWidth())
                else:  # horizontal with spacing
                    # Sort by x position
                    nodes.sort(key=lambda n: n.xpos())
                    x_pos = nodes[0].xpos()
                    for node in nodes:
                        node.setXpos(x_pos)
                        x_pos += node.screenWidth() + spacing
            
            elif alignment in ['top', 'bottom', 'vertical']:
                # Sort by x position
                nodes.sort(key=lambda n: n.xpos())
                
                # Align
                if alignment == 'top':
                    y_pos = min(n.ypos() for n in nodes)
                    for node in nodes:
                        node.setYpos(y_pos)
                elif alignment == 'bottom':
                    y_pos = max(n.ypos() + n.screenHeight() for n in nodes)
                    for node in nodes:
                        node.setYpos(y_pos - node.screenHeight())
                else:  # vertical with spacing
                    # Sort by y position
                    nodes.sort(key=lambda n: n.ypos())
                    y_pos = nodes[0].ypos()
                    for node in nodes:
                        node.setYpos(y_pos)
                        y_pos += node.screenHeight() + spacing
            
            logger.debug(f"Aligned {len(nodes)} nodes {alignment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to align nodes: {e}")
            return False
    
    def distribute_nodes(self, nodes: List['nuke.Node'] = None,
                        direction: str = 'horizontal',
                        spacing: int = 100) -> bool:
        """
        Distribute nodes evenly
        
        Args:
            nodes: Nodes to distribute (None for selected nodes)
            direction: 'horizontal' or 'vertical'
            spacing: Spacing between nodes
            
        Returns:
            Success status
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if len(nodes) < 2:
                return False
            
            if direction == 'horizontal':
                # Sort by x position
                nodes.sort(key=lambda n: n.xpos())
                
                # Get bounds
                min_x = min(n.xpos() for n in nodes)
                max_x = max(n.xpos() for n in nodes)
                
                # Calculate positions
                total_width = max_x - min_x
                if len(nodes) > 1:
                    step = total_width / (len(nodes) - 1)
                else:
                    step = 0
                
                # Distribute
                for i, node in enumerate(nodes):
                    target_x = min_x + i * step
                    node.setXpos(int(target_x))
            
            else:  # vertical
                # Sort by y position
                nodes.sort(key=lambda n: n.ypos())
                
                # Get bounds
                min_y = min(n.ypos() for n in nodes)
                max_y = max(n.ypos() for n in nodes)
                
                # Calculate positions
                total_height = max_y - min_y
                if len(nodes) > 1:
                    step = total_height / (len(nodes) - 1)
                else:
                    step = 0
                
                # Distribute
                for i, node in enumerate(nodes):
                    target_y = min_y + i * step
                    node.setYpos(int(target_y))
            
            logger.debug(f"Distributed {len(nodes)} nodes {direction}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to distribute nodes: {e}")
            return False
    
    def scale_nodes(self, nodes: List['nuke.Node'] = None,
                   scale_factor: float = 1.0,
                   origin: Tuple[int, int] = None) -> bool:
        """
        Scale node positions
        
        Args:
            nodes: Nodes to scale (None for selected nodes)
            scale_factor: Scaling factor
            origin: Scaling origin point (None for centroid)
            
        Returns:
            Success status
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                return False
            
            # Calculate origin if not provided
            if origin is None:
                x_positions = [n.xpos() for n in nodes]
                y_positions = [n.ypos() for n in nodes]
                origin = (
                    sum(x_positions) // len(x_positions),
                    sum(y_positions) // len(y_positions)
                )
            
            origin_x, origin_y = origin
            
            # Scale positions
            for node in nodes:
                current_x = node.xpos()
                current_y = node.ypos()
                
                # Calculate vector from origin
                vec_x = current_x - origin_x
                vec_y = current_y - origin_y
                
                # Scale vector
                vec_x *= scale_factor
                vec_y *= scale_factor
                
                # Calculate new position
                new_x = origin_x + int(vec_x)
                new_y = origin_y + int(vec_y)
                
                node.setXpos(new_x)
                node.setYpos(new_y)
            
            logger.debug(f"Scaled {len(nodes)} nodes by factor {scale_factor}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale nodes: {e}")
            return False
    
    def rotate_nodes(self, nodes: List['nuke.Node'] = None,
                    angle_degrees: float = 0,
                    origin: Tuple[int, int] = None) -> bool:
        """
        Rotate node positions
        
        Args:
            nodes: Nodes to rotate (None for selected nodes)
            angle_degrees: Rotation angle in degrees
            origin: Rotation origin point (None for centroid)
            
        Returns:
            Success status
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                return False
            
            # Convert angle to radians
            angle_rad = math.radians(angle_degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            # Calculate origin if not provided
            if origin is None:
                x_positions = [n.xpos() for n in nodes]
                y_positions = [n.ypos() for n in nodes]
                origin = (
                    sum(x_positions) // len(x_positions),
                    sum(y_positions) // len(y_positions)
                )
            
            origin_x, origin_y = origin
            
            # Rotate positions
            for node in nodes:
                current_x = node.xpos()
                current_y = node.ypos()
                
                # Calculate vector from origin
                vec_x = current_x - origin_x
                vec_y = current_y - origin_y
                
                # Rotate vector
                new_x = vec_x * cos_a - vec_y * sin_a
                new_y = vec_x * sin_a + vec_y * cos_a
                
                # Calculate new position
                new_x = origin_x + int(new_x)
                new_y = origin_y + int(new_y)
                
                node.setXpos(new_x)
                node.setYpos(new_y)
            
            logger.debug(f"Rotated {len(nodes)} nodes by {angle_degrees} degrees")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate nodes: {e}")
            return False
    
    def mirror_nodes(self, nodes: List['nuke.Node'] = None,
                    axis: str = 'vertical',
                    origin: Tuple[int, int] = None) -> bool:
        """
        Mirror node positions
        
        Args:
            nodes: Nodes to mirror (None for selected nodes)
            axis: 'vertical', 'horizontal', or 'both'
            origin: Mirror axis/point (None for centroid)
            
        Returns:
            Success status
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                return False
            
            # Calculate origin if not provided
            if origin is None:
                x_positions = [n.xpos() for n in nodes]
                y_positions = [n.ypos() for n in nodes]
                origin = (
                    sum(x_positions) // len(x_positions),
                    sum(y_positions) // len(y_positions)
                )
            
            origin_x, origin_y = origin
            
            # Mirror positions
            for node in nodes:
                current_x = node.xpos()
                current_y = node.ypos()
                
                if axis in ['vertical', 'both']:
                    # Mirror vertically (across x-axis)
                    distance_x = current_x - origin_x
                    new_x = origin_x - distance_x
                    node.setXpos(new_x)
                
                if axis in ['horizontal', 'both']:
                    # Mirror horizontally (across y-axis)
                    distance_y = current_y - origin_y
                    new_y = origin_y - distance_y
                    node.setYpos(new_y)
            
            logger.debug(f"Mirrored {len(nodes)} nodes across {axis} axis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mirror nodes: {e}")
            return False
    
    def set_node_disabled(self, node: 'nuke.Node', disabled: bool = True) -> bool:
        """Enable or disable a node"""
        try:
            disable_knob = node.knob('disable')
            if disable_knob:
                disable_knob.setValue(disabled)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set node disabled: {e}")
            return False
    
    def toggle_nodes_disabled(self, nodes: List['nuke.Node'] = None) -> Dict[str, bool]:
        """
        Toggle disabled state of nodes
        
        Args:
            nodes: Nodes to toggle (None for selected nodes)
            
        Returns:
            Dictionary mapping node names to new disabled state
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            results = {}
            
            for node in nodes:
                disable_knob = node.knob('disable')
                if disable_knob:
                    current = disable_knob.value()
                    new_state = not current
                    disable_knob.setValue(new_state)
                    results[node.name()] = new_state
            
            logger.debug(f"Toggled disabled state for {len(results)} nodes")
            return results
            
        except Exception as e:
            logger.error(f"Failed to toggle nodes disabled: {e}")
            return {}
    
    def _get_color_for_node_class(self, node_class: str) -> int:
        """Get appropriate color for a node class"""
        node_class_lower = node_class.lower()
        
        # Check for specific node types
        if 'read' in node_class_lower:
            return COLOR_INPUT
        elif 'write' in node_class_lower:
            return COLOR_OUTPUT
        elif 'viewer' in node_class_lower:
            return COLOR_OUTPUT
        elif 'transform' in node_class_lower:
            return COLOR_TRANSFORM
        elif any(x in node_class_lower for x in ['grade', 'color', 'lut']):
            return COLOR_EFFECT
        elif any(x in node_class_lower for x in ['merge', 'mix', 'switch']):
            return COLOR_EFFECT
        elif '3d' in node_class_lower or any(x in node_class_lower for x in ['camera', 'axis', 'geometry']):
            return COLOR_3D
        elif 'group' in node_class_lower or 'gizmo' in node_class_lower:
            return COLOR_GROUP
        else:
            return COLOR_UTILITY
    
    def _ensure_unique_name(self, name: str, node: 'nuke.Node') -> str:
        """Ensure node name is unique"""
        original_name = name
        counter = 1
        
        while True:
            # Check if name exists (excluding the node itself)
            existing = nuke.toNode(name)
            if not existing or existing == node:
                return name
            
            # Try with incrementing counter
            name = f"{original_name}_{counter}"
            counter += 1

# Helper functions
def set_node_color(node: 'nuke.Node', color: Union[int, str]) -> bool:
    """Helper function to set node color"""
    modifier = NodeModifier()
    return modifier.set_node_color(node, color)

def rename_nodes(nodes: List['nuke.Node'] = None, **kwargs) -> Dict[str, str]:
    """Helper function to rename nodes"""
    modifier = NodeModifier()
    return modifier.rename_nodes(nodes, **kwargs)

def align_nodes(nodes: List['nuke.Node'] = None, **kwargs) -> bool:
    """Helper function to align nodes"""
    modifier = NodeModifier()
    return modifier.align_nodes(nodes, **kwargs)