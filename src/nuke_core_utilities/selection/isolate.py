"""
Node isolation and focus utilities
"""

from typing import List, Optional, Dict, Any
import nuke

from ..core.logging_utils import get_logger
from ..core.constants import *
from ..graph.traversal import GraphTraversal
from ..selection.selection import SelectionManager

logger = get_logger(__name__)

class IsolationManager:
    """Node isolation and focus utilities"""
    
    def __init__(self):
        self.traversal = GraphTraversal()
        self.selection = SelectionManager()
        self.isolation_state = {}
    
    def isolate_nodes(self, nodes: List['nuke.Node'],
                     show_connections: bool = True,
                     hide_others: bool = True) -> Dict[str, Any]:
        """
        Isolate selected nodes
        
        Args:
            nodes: Nodes to isolate
            show_connections: Show connected nodes
            hide_others: Hide other nodes
            
        Returns:
            Isolation results
        """
        try:
            if not nodes:
                return {'isolated': 0, 'hidden': 0, 'error': 'No nodes to isolate'}
            
            # Store current state
            self._store_isolation_state()
            
            # Get all nodes in the graph
            all_nodes = nuke.allNodes()
            
            # Determine which nodes to show
            nodes_to_show = set(nodes)
            
            if show_connections:
                # Add connected nodes
                for node in nodes:
                    # Add upstream and downstream
                    upstream = self.traversal.get_upstream_nodes(node, include_self=False)
                    downstream = self.traversal.get_downstream_nodes(node, include_self=False)
                    nodes_to_show.update(upstream)
                    nodes_to_show.update(downstream)
            
            # Determine which nodes to hide
            if hide_others:
                nodes_to_hide = [n for n in all_nodes if n not in nodes_to_show]
            else:
                nodes_to_hide = []
            
            # Apply visibility
            hidden_count = self._set_nodes_visible(nodes_to_hide, False)
            shown_count = self._set_nodes_visible(nodes_to_show, True)
            
            # Select the original nodes
            self.selection.clear_selection()
            for node in nodes:
                node.setSelected(True)
            
            # Center view on isolated nodes
            self._center_view_on_nodes(nodes)
            
            result = {
                'isolated': len(nodes),
                'shown': shown_count,
                'hidden': hidden_count,
                'nodes': [n.name() for n in nodes]
            }
            
            logger.info(f"Isolated {len(nodes)} nodes (shown: {shown_count}, hidden: {hidden_count})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to isolate nodes: {e}")
            return {'error': str(e)}
    
    def isolate_selection(self, show_connections: bool = True,
                         hide_others: bool = True) -> Dict[str, Any]:
        """
        Isolate currently selected nodes
        
        Args:
            show_connections: Show connected nodes
            hide_others: Hide other nodes
            
        Returns:
            Isolation results
        """
        try:
            selected_nodes = nuke.selectedNodes()
            return self.isolate_nodes(selected_nodes, show_connections, hide_others)
            
        except Exception as e:
            logger.error(f"Failed to isolate selection: {e}")
            return {'error': str(e)}
    
    def isolate_by_type(self, node_classes: List[str],
                       show_connections: bool = False) -> Dict[str, Any]:
        """
        Isolate nodes by type
        
        Args:
            node_classes: List of node classes to isolate
            show_connections: Show connected nodes
            
        Returns:
            Isolation results
        """
        try:
            # Find nodes of specified types
            nodes_to_isolate = []
            for node_class in node_classes:
                nodes = nuke.allNodes(node_class)
                nodes_to_isolate.extend(nodes)
            
            if not nodes_to_isolate:
                return {'isolated': 0, 'warning': 'No nodes found'}
            
            return self.isolate_nodes(nodes_to_isolate, show_connections, hide_others=True)
            
        except Exception as e:
            logger.error(f"Failed to isolate by type: {e}")
            return {'error': str(e)}
    
    def show_all_nodes(self) -> Dict[str, Any]:
        """Show all hidden nodes"""
        try:
            # Get all nodes
            all_nodes = nuke.allNodes()
            
            # Show all nodes
            shown_count = self._set_nodes_visible(all_nodes, True)
            
            result = {
                'shown': shown_count,
                'message': f'Showed {shown_count} nodes'
            }
            
            # Clear isolation state
            self.isolation_state.clear()
            
            logger.info(f"Showed all {shown_count} nodes")
            return result
            
        except Exception as e:
            logger.error(f"Failed to show all nodes: {e}")
            return {'error': str(e)}
    
    def restore_isolation_state(self) -> Dict[str, Any]:
        """Restore previous isolation state"""
        try:
            if not self.isolation_state:
                return {'restored': 0, 'message': 'No state to restore'}
            
            restored_count = 0
            
            for node_name, was_visible in self.isolation_state.items():
                node = nuke.toNode(node_name)
                if node:
                    try:
                        node['hide_input'].setValue(not was_visible)
                        restored_count += 1
                    except:
                        pass
            
            result = {
                'restored': restored_count,
                'message': f'Restored visibility for {restored_count} nodes'
            }
            
            # Clear state
            self.isolation_state.clear()
            
            logger.info(f"Restored isolation state for {restored_count} nodes")
            return result
            
        except Exception as e:
            logger.error(f"Failed to restore isolation state: {e}")
            return {'error': str(e)}
    
    def focus_on_node(self, node: 'nuke.Node',
                     zoom_level: float = 1.0) -> bool:
        """
        Focus view on a specific node
        
        Args:
            node: Node to focus on
            zoom_level: Zoom level (1.0 = fit to screen)
            
        Returns:
            Success status
        """
        try:
            # Select the node
            self.selection.clear_selection()
            node.setSelected(True)
            
            # Center view
            self._center_view_on_nodes([node], zoom_level)
            
            logger.debug(f"Focused on node: {node.name()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to focus on node: {e}")
            return False
    
    def create_isolation_group(self, nodes: List['nuke.Node'] = None,
                              name: str = "Isolation_Group") -> Optional['nuke.Group']:
        """
        Create a group from isolated nodes
        
        Args:
            nodes: Nodes to group (None for selected nodes)
            name: Group name
            
        Returns:
            Created group or None
        """
        try:
            if nodes is None:
                nodes = nuke.selectedNodes()
            
            if not nodes:
                return None
            
            # Create group
            from ..nodes.create import NodeCreator
            creator = NodeCreator()
            group = creator.create_node_group(nodes, name=name)
            
            if group:
                # Isolate the group
                self.isolate_nodes([group], show_connections=False, hide_others=True)
                
                logger.info(f"Created isolation group '{name}' with {len(nodes)} nodes")
                return group
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create isolation group: {e}")
            return None
    
    def _store_isolation_state(self):
        """Store current node visibility state"""
        try:
            self.isolation_state.clear()
            
            for node in nuke.allNodes():
                try:
                    hide_input_knob = node.knob('hide_input')
                    if hide_input_knob:
                        is_hidden = hide_input_knob.value()
                        self.isolation_state[node.name()] = not is_hidden
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to store isolation state: {e}")
    
    def _set_nodes_visible(self, nodes: List['nuke.Node'], visible: bool) -> int:
        """Set visibility for multiple nodes"""
        count = 0
        
        for node in nodes:
            try:
                hide_input_knob = node.knob('hide_input')
                if hide_input_knob:
                    hide_input_knob.setValue(not visible)
                    count += 1
            except:
                pass
        
        return count
    
    def _center_view_on_nodes(self, nodes: List['nuke.Node'], 
                            zoom_level: float = 1.0):
        """Center graph view on nodes"""
        try:
            if not nodes:
                return
            
            # Calculate bounding box
            x_positions = [n.xpos() for n in nodes]
            y_positions = [n.ypos() for n in nodes]
            
            min_x = min(x_positions)
            max_x = max(x_positions)
            min_y = min(y_positions)
            max_y = max(y_positions)
            
            # Add some padding
            padding = 100
            min_x -= padding
            max_x += padding
            min_y -= padding
            max_y += padding
            
            # Calculate center
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            
            # This would require Nuke Python API for view manipulation
            # Currently, Nuke's Python API doesn't provide direct access to pan/zoom
            # We can only select nodes and let users manually frame them
            
            # For now, we'll just log the suggested view
            logger.debug(f"Suggested view: center=({center_x}, {center_y}), zoom={zoom_level}")
            
        except Exception as e:
            logger.warning(f"Failed to center view: {e}")

# Helper functions
def isolate_nodes(nodes: List['nuke.Node'], **kwargs) -> Dict[str, Any]:
    """Helper function to isolate nodes"""
    manager = IsolationManager()
    return manager.isolate_nodes(nodes, **kwargs)

def isolate_selection(**kwargs) -> Dict[str, Any]:
    """Helper function to isolate selection"""
    manager = IsolationManager()
    return manager.isolate_selection(**kwargs)

def show_all_nodes() -> Dict[str, Any]:
    """Helper function to show all nodes"""
    manager = IsolationManager()
    return manager.show_all_nodes()

def focus_on_node(node: 'nuke.Node', **kwargs) -> bool:
    """Helper function to focus on node"""
    manager = IsolationManager()
    return manager.focus_on_node(node, **kwargs)