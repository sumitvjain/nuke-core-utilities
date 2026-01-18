"""
Node selection management utilities
"""

from typing import Dict, List, Optional, Set, Any
import nuke

from ..core.logging_utils import get_logger
from ..core.constants import *
from ..graph.traversal import GraphTraversal
from ..graph.connections import ConnectionManager

logger = get_logger(__name__)

class SelectionManager:
    """Advanced node selection management"""
    
    def __init__(self):
        self.traversal = GraphTraversal()
        self.connections = ConnectionManager()
    
    def select_by_criteria(self, criteria: Dict[str, Any],
                          add_to_selection: bool = False) -> List['nuke.Node']:
        """
        Select nodes by multiple criteria
        
        Args:
            criteria: Dictionary of selection criteria
            add_to_selection: Add to current selection (False replaces)
            
        Returns:
            List of selected nodes
        """
        try:
            # Get all nodes
            all_nodes = nuke.allNodes()
            selected = []
            
            for node in all_nodes:
                if self._node_matches_criteria(node, criteria):
                    selected.append(node)
            
            # Apply selection
            if not add_to_selection:
                nuke.selectAll()
                nuke.invertSelection()
            
            for node in selected:
                node.setSelected(True)
            
            logger.debug(f"Selected {len(selected)} nodes by criteria")
            return selected
            
        except Exception as e:
            logger.error(f"Failed to select by criteria: {e}")
            return []
    
    def select_connected(self, direction: str = 'both',
                        include_self: bool = True) -> List['nuke.Node']:
        """
        Select connected nodes
        
        Args:
            direction: 'inputs', 'outputs', or 'both'
            include_self: Include selected nodes in result
            
        Returns:
            List of selected nodes
        """
        try:
            selected_nodes = nuke.selectedNodes()
            if not selected_nodes:
                return []
            
            connected = set()
            
            for node in selected_nodes:
                if direction in ['inputs', 'both']:
                    upstream = self.traversal.bfs_traversal(node, direction='backward')
                    connected.update(upstream)
                
                if direction in ['outputs', 'both']:
                    downstream = self.traversal.bfs_traversal(node, direction='forward')
                    connected.update(downdownstream)
            
            if not include_self:
                connected.difference_update(selected_nodes)
            
            # Apply selection
            nuke.selectAll()
            nuke.invertSelection()
            for node in connected:
                node.setSelected(True)
            
            logger.debug(f"Selected {len(connected)} connected nodes")
            return list(connected)
            
        except Exception as e:
            logger.error(f"Failed to select connected: {e}")
            return []
    
    def select_by_type(self, node_classes: List[str],
                      add_to_selection: bool = False) -> List['nuke.Node']:
        """
        Select nodes by type
        
        Args:
            node_classes: List of node classes to select
            add_to_selection: Add to current selection
            
        Returns:
            List of selected nodes
        """
        try:
            selected = []
            
            for node_class in node_classes:
                nodes = nuke.allNodes(node_class)
                selected.extend(nodes)
            
            # Apply selection
            if not add_to_selection:
                nuke.selectAll()
                nuke.invertSelection()
            
            for node in selected:
                node.setSelected(True)
            
            logger.debug(f"Selected {len(selected)} nodes by type")
            return selected
            
        except Exception as e:
            logger.error(f"Failed to select by type: {e}")
            return []
    
    def select_by_name_pattern(self, pattern: str,
                              use_regex: bool = False,
                              add_to_selection: bool = False) -> List['nuke.Node']:
        """
        Select nodes by name pattern
        
        Args:
            pattern: Name pattern
            use_regex: Use regex pattern matching
            add_to_selection: Add to current selection
            
        Returns:
            List of selected nodes
        """
        try:
            import re
            
            all_nodes = nuke.allNodes()
            selected = []
            
            for node in all_nodes:
                node_name = node.name()
                
                if use_regex:
                    if re.search(pattern, node_name):
                        selected.append(node)
                else:
                    if pattern in node_name:
                        selected.append(node)
            
            # Apply selection
            if not add_to_selection:
                nuke.selectAll()
                nuke.invertSelection()
            
            for node in selected:
                node.setSelected(True)
            
            logger.debug(f"Selected {len(selected)} nodes by name pattern")
            return selected
            
        except Exception as e:
            logger.error(f"Failed to select by name pattern: {e}")
            return []
    
    def select_island(self, include_backdrops: bool = True) -> List['nuke.Node']:
        """
        Select entire connected island
        
        Args:
            include_backdrops: Include backdrop nodes
            
        Returns:
            List of selected nodes
        """
        try:
            selected_nodes = nuke.selectedNodes()
            if not selected_nodes:
                return []
            
            # Get all nodes in the same island
            island_nodes = set()
            
            for node in selected_nodes:
                island = self.traversal.get_island_nodes(node)
                island_nodes.update(island)
            
            # Filter out backdrops if not wanted
            if not include_backdrops:
                island_nodes = {n for n in island_nodes if n.Class() != 'BackdropNode'}
            
            # Apply selection
            nuke.selectAll()
            nuke.invertSelection()
            for node in island_nodes:
                node.setSelected(True)
            
            logger.debug(f"Selected {len(island_nodes)} island nodes")
            return list(island_nodes)
            
        except Exception as e:
            logger.error(f"Failed to select island: {e}")
            return []
    
    def invert_selection(self) -> List['nuke.Node']:
        """Invert current selection"""
        try:
            # Get currently selected
            current_selected = nuke.selectedNodes()
            
            # Invert
            nuke.selectAll()
            nuke.invertSelection()
            
            # Get new selection
            new_selected = nuke.selectedNodes()
            
            logger.debug(f"Inverted selection: {len(current_selected)} -> {len(new_selected)} nodes")
            return new_selected
            
        except Exception as e:
            logger.error(f"Failed to invert selection: {e}")
            return []
    
    def select_similar(self, criteria: List[str] = None) -> List['nuke.Node']:
        """
        Select nodes similar to currently selected
        
        Args:
            criteria: List of criteria to match ('class', 'color', 'position', 'connections')
            
        Returns:
            List of selected nodes
        """
        try:
            selected_nodes = nuke.selectedNodes()
            if not selected_nodes:
                return []
            
            if criteria is None:
                criteria = ['class', 'color']
            
            # Use first selected node as reference
            reference = selected_nodes[0]
            reference_info = self._get_node_comparison_info(reference, criteria)
            
            all_nodes = nuke.allNodes()
            similar = []
            
            for node in all_nodes:
                if node in selected_nodes:
                    continue
                
                node_info = self._get_node_comparison_info(node, criteria)
                if self._info_matches(reference_info, node_info, criteria):
                    similar.append(node)
            
            # Add similar nodes to selection
            for node in similar:
                node.setSelected(True)
            
            logger.debug(f"Selected {len(similar)} similar nodes")
            return selected_nodes + similar
            
        except Exception as e:
            logger.error(f"Failed to select similar: {e}")
            return []
    
    def clear_selection(self) -> bool:
        """Clear all selection"""
        try:
            nuke.selectAll()
            nuke.invertSelection()
            logger.debug("Cleared selection")
            return True
        except Exception as e:
            logger.error(f"Failed to clear selection: {e}")
            return False
    
    def get_selection_info(self) -> Dict[str, Any]:
        """Get information about current selection"""
        try:
            selected = nuke.selectedNodes()
            
            info = {
                'count': len(selected),
                'nodes': [],
                'statistics': defaultdict(int)
            }
            
            for node in selected:
                node_info = {
                    'name': node.name(),
                    'class': node.Class(),
                    'position': (node.xpos(), node.ypos())
                }
                info['nodes'].append(node_info)
                info['statistics'][node.Class()] += 1
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get selection info: {e}")
            return {}
    
    def _node_matches_criteria(self, node: 'nuke.Node', criteria: Dict[str, Any]) -> bool:
        """Check if node matches selection criteria"""
        try:
            # Check class
            if 'class' in criteria:
                target_classes = criteria['class']
                if isinstance(target_classes, str):
                    target_classes = [target_classes]
                if node.Class() not in target_classes:
                    return False
            
            # Check name pattern
            if 'name_pattern' in criteria:
                import re
                pattern = criteria['name_pattern']
                if not re.search(pattern, node.name()):
                    return False
            
            # Check position
            if 'position_range' in criteria:
                x_range, y_range = criteria['position_range']
                if not (x_range[0] <= node.xpos() <= x_range[1] and
                       y_range[0] <= node.ypos() <= y_range[1]):
                    return False
            
            # Check color
            if 'color' in criteria:
                color_knob = node.knob('tile_color')
                if not color_knob or color_knob.value() != criteria['color']:
                    return False
            
            # Check disabled state
            if 'disabled' in criteria:
                disable_knob = node.knob('disable')
                is_disabled = disable_knob and disable_knob.value()
                if is_disabled != criteria['disabled']:
                    return False
            
            # Check connections
            if 'min_inputs' in criteria:
                if node.inputs() < criteria['min_inputs']:
                    return False
            
            if 'max_inputs' in criteria:
                if node.inputs() > criteria['max_inputs']:
                    return False
            
            if 'min_outputs' in criteria:
                if len(node.dependent()) < criteria['min_outputs']:
                    return False
            
            if 'max_outputs' in criteria:
                if len(node.dependent()) > criteria['max_outputs']:
                    return False
            
            return True
            
        except:
            return False
    
    def _get_node_comparison_info(self, node: 'nuke.Node', criteria: List[str]) -> Dict[str, Any]:
        """Get node information for comparison"""
        info = {}
        
        if 'class' in criteria:
            info['class'] = node.Class()
        
        if 'color' in criteria:
            color_knob = node.knob('tile_color')
            info['color'] = color_knob.value() if color_knob else 0
        
        if 'position' in criteria:
            info['position'] = (node.xpos(), node.ypos())
        
        if 'connections' in criteria:
            info['inputs'] = node.inputs()
            info['outputs'] = len(node.dependent())
        
        return info
    
    def _info_matches(self, info1: Dict[str, Any], info2: Dict[str, Any], criteria: List[str]) -> bool:
        """Check if node information matches"""
        for criterion in criteria:
            if criterion in info1 and criterion in info2:
                if info1[criterion] != info2[criterion]:
                    return False
        return True

# Helper functions
def select_by_criteria(criteria: Dict[str, Any], **kwargs) -> List['nuke.Node']:
    """Helper function to select by criteria"""
    manager = SelectionManager()
    return manager.select_by_criteria(criteria, **kwargs)

def select_connected(direction: str = 'both', **kwargs) -> List['nuke.Node']:
    """Helper function to select connected nodes"""
    manager = SelectionManager()
    return manager.select_connected(direction, **kwargs)

def select_by_type(node_classes: List[str], **kwargs) -> List['nuke.Node']:
    """Helper function to select by type"""
    manager = SelectionManager()
    return manager.select_by_type(node_classes, **kwargs)

def clear_selection() -> bool:
    """Helper function to clear selection"""
    manager = SelectionManager()
    return manager.clear_selection()