"""
Node deletion utilities
"""

from typing import List, Optional, Dict, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..graph.connections import ConnectionManager
from ..data.cache import get_cache

logger = get_logger(__name__)

class NodeDeleter:
    """Safe node deletion with cleanup"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.cache = get_cache()
    
    def delete_nodes(self, nodes: List['nuke.Node'] = None,
                    cleanup_connections: bool = True,
                    backup: bool = True,
                    force: bool = False) -> Dict[str, Any]:
        """
        Delete nodes with options
        
        Args:
            nodes: Nodes to delete (None for selected nodes)
            cleanup_connections: Reconnect inputs to outputs
            backup: Create backup before deletion
            force: Skip confirmation
            
        Returns:
            Dictionary with deletion results
        """
        with TimerContext("delete_nodes", logger):
            try:
                if nodes is None:
                    nodes = nuke.selectedNodes()
                
                if not nodes:
                    return {'deleted': 0, 'errors': 0, 'message': 'No nodes to delete'}
                
                # Get confirmation if not forced
                if not force and len(nodes) > 5:
                    if not nuke.ask(f"Delete {len(nodes)} nodes?"):
                        return {'deleted': 0, 'errors': 0, 'message': 'Cancelled by user'}
                
                # Create backup if requested
                if backup:
                    self._create_deletion_backup(nodes)
                
                # Store node info for logging
                node_info = []
                for node in nodes:
                    node_info.append({
                        'name': node.name(),
                        'class': node.Class(),
                        'inputs': node.inputs(),
                        'dependents': len(node.dependent())
                    })
                
                # Handle connections if requested
                if cleanup_connections:
                    self._cleanup_connections_before_deletion(nodes)
                
                # Delete nodes
                deleted_count = 0
                error_count = 0
                
                for node in nodes[:]:  # Copy list as it might change
                    try:
                        nuke.delete(node)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete node {node.name()}: {e}")
                        error_count += 1
                
                # Clear cache for deleted nodes
                self._clear_node_cache(nodes)
                
                result = {
                    'deleted': deleted_count,
                    'errors': error_count,
                    'total': len(nodes),
                    'node_info': node_info,
                    'success': error_count == 0
                }
                
                logger.info(f"Deleted {deleted_count} nodes ({error_count} errors)")
                return result
                
            except Exception as e:
                logger.error(f"Failed to delete nodes: {e}")
                return {'deleted': 0, 'errors': 1, 'message': str(e)}
    
    def delete_orphaned_nodes(self, nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
        """
        Delete orphaned nodes (not connected to main graph)
        
        Args:
            nodes: Nodes to check (None for all nodes)
            
        Returns:
            Dictionary with deletion results
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes()
            
            # Find Viewer nodes
            viewer_nodes = nuke.allNodes('Viewer')
            viewer_islands = set()
            
            # Get all nodes connected to Viewers
            for viewer in viewer_nodes:
                island = self.connection_manager.get_island_nodes(viewer)
                viewer_islands.update(island)
            
            # Find orphaned nodes (not in viewer islands)
            orphaned = [n for n in nodes if n not in viewer_islands]
            
            # Also remove Viewers themselves from orphaned list
            orphaned = [n for n in orphaned if n.Class() != 'Viewer']
            
            if not orphaned:
                return {'deleted': 0, 'errors': 0, 'message': 'No orphaned nodes found'}
            
            # Delete orphaned nodes
            return self.delete_nodes(orphaned, cleanup_connections=False)
            
        except Exception as e:
            logger.error(f"Failed to delete orphaned nodes: {e}")
            return {'deleted': 0, 'errors': 1, 'message': str(e)}
    
    def delete_by_type(self, node_classes: List[str],
                      exclude_nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
        """
        Delete nodes by type
        
        Args:
            node_classes: List of node classes to delete
            exclude_nodes: Nodes to exclude from deletion
            
        Returns:
            Dictionary with deletion results
        """
        try:
            nodes_to_delete = []
            
            for node_class in node_classes:
                nodes = nuke.allNodes(node_class)
                
                if exclude_nodes:
                    nodes = [n for n in nodes if n not in exclude_nodes]
                
                nodes_to_delete.extend(nodes)
            
            
            if not nodes_to_delete:
                return {'deleted': 0, 'errors': 0, 'message': 'No matching nodes found'}
            
            # Delete the nodes
            return self.delete_nodes(nodes_to_delete, cleanup_connections=True)
            
        except Exception as e:
            logger.error(f"Failed to delete by type: {e}")
            return {'deleted': 0, 'errors': 1, 'message': str(e)}
    
    def delete_by_pattern(self, name_pattern: str,
                         use_regex: bool = False,
                         case_sensitive: bool = False) -> Dict[str, Any]:
        """
        Delete nodes by name pattern
        
        Args:
            name_pattern: Pattern to match node names
            use_regex: Use regex pattern matching
            case_sensitive: Case-sensitive matching
            
        Returns:
            Dictionary with deletion results
        """
        try:
            import re
            
            nodes_to_delete = []
            
            for node in nuke.allNodes():
                node_name = node.name()
                
                if not case_sensitive:
                    node_name = node_name.lower()
                    name_pattern = name_pattern.lower()
                
                if use_regex:
                    if re.search(name_pattern, node_name):
                        nodes_to_delete.append(node)
                else:
                    if name_pattern in node_name:
                        nodes_to_delete.append(node)
            
            if not nodes_to_delete:
                return {'deleted': 0, 'errors': 0, 'message': 'No matching nodes found'}
            
            # Delete the nodes
            return self.delete_nodes(nodes_to_delete, cleanup_connections=True)
            
        except Exception as e:
            logger.error(f"Failed to delete by pattern: {e}")
            return {'deleted': 0, 'errors': 1, 'message': str(e)}
    
    def delete_duplicate_nodes(self, nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
        """
        Delete duplicate nodes (same class, position, and connections)
        
        Args:
            nodes: Nodes to check (None for all nodes)
            
        Returns:
            Dictionary with deletion results
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes()
            
            # Group nodes by signature
            node_signatures = {}
            duplicates = []
            
            for node in nodes:
                # Create signature based on class, position, and connections
                signature = self._get_node_signature(node)
                
                if signature in node_signatures:
                    # Found a duplicate
                    duplicates.append(node)
                else:
                    node_signatures[signature] = node
            
            if not duplicates:
                return {'deleted': 0, 'errors': 0, 'message': 'No duplicate nodes found'}
            
            # Delete duplicate nodes (keep the first one)
            return self.delete_nodes(duplicates, cleanup_connections=True)
            
        except Exception as e:
            logger.error(f"Failed to delete duplicate nodes: {e}")
            return {'deleted': 0, 'errors': 1, 'message': str(e)}
    
    def delete_unused_inputs(self, nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
        """
        Delete nodes with no connections (dangling inputs/outputs)
        
        Args:
            nodes: Nodes to check (None for all nodes)
            
        Returns:
            Dictionary with deletion results
        """
        try:
            if nodes is None:
                nodes = nuke.allNodes()
            
            unused_nodes = []
            
            for node in nodes:
                # Check if node has no inputs and no outputs
                has_inputs = any(node.input(i) is not None for i in range(node.inputs()))
                has_outputs = len(node.dependent()) > 0
                
                if not has_inputs and not has_outputs:
                    unused_nodes.append(node)
            
            if not unused_nodes:
                return {'deleted': 0, 'errors': 0, 'message': 'No unused nodes found'}
            
            # Delete unused nodes
            return self.delete_nodes(unused_nodes, cleanup_connections=False)
            
        except Exception as e:
            logger.error(f"Failed to delete unused nodes: {e}")
            return {'deleted': 0, 'errors': 1, 'message': str(e)}
    
    def _create_deletion_backup(self, nodes: List['nuke.Node']):
        """Create backup of nodes before deletion"""
        try:
            # Store node information in cache
            node_data = []
            for node in nodes:
                node_data.append({
                    'name': node.name(),
                    'class': node.Class(),
                    'position': (node.xpos(), node.ypos()),
                    'knobs': self._extract_knob_values(node)
                })
            
            # Save to cache
            self.cache.set('deletion_backup', node_data, ttl=3600)  # 1 hour
            
            logger.debug(f"Created backup for {len(nodes)} nodes")
            
        except Exception as e:
            logger.warning(f"Failed to create deletion backup: {e}")
    
    def _cleanup_connections_before_deletion(self, nodes: List['nuke.Node']):
        """Reconnect nodes around deleted nodes"""
        try:
            # For each node to delete, reconnect its inputs to its outputs
            for node in nodes:
                inputs = []
                for i in range(node.inputs()):
                    input_node = node.input(i)
                    if input_node:
                        inputs.append((i, input_node))
                
                outputs = defaultdict(list)
                for dependent in node.dependent():
                    for i in range(dependent.inputs()):
                        if dependent.input(i) == node:
                            outputs[i].append(dependent)
                
                # Reconnect inputs to outputs
                for output_idx, dependents in outputs.items():
                    if inputs:  # Has inputs to connect from
                        source_input_idx, source_node = inputs[0]  # Use first input
                        for dependent in dependents:
                            dependent.setInput(output_idx, source_node)
            
        except Exception as e:
            logger.warning(f"Failed to cleanup connections: {e}")
    
    def _clear_node_cache(self, nodes: List['nuke.Node']):
        """Clear cache entries for deleted nodes"""
        try:
            cache = get_cache()
            for node in nodes:
                # Clear any cached data for this node
                for key in list(cache.cache.keys()):
                    if f"node:{node.name()}" in key:
                        cache.delete(key)
        except Exception as e:
            logger.warning(f"Failed to clear node cache: {e}")
    
    def _extract_knob_values(self, node: 'nuke.Node') -> Dict:
        """Extract knob values from node"""
        knob_values = {}
        for knob_name in node.knobs():
            knob = node.knob(knob_name)
            if knob:
                try:
                    knob_values[knob_name] = knob.value()
                except:
                    pass
        return knob_values
    
    def _get_node_signature(self, node: 'nuke.Node') -> str:
        """Create unique signature for a node"""
        signature_parts = [
            node.Class(),
            str(node.xpos()),
            str(node.ypos())
        ]
        
        # Add connection information
        inputs = []
        for i in range(node.inputs()):
            input_node = node.input(i)
            inputs.append(input_node.name() if input_node else "None")
        
        signature_parts.extend(inputs)
        
        # Add knob values for critical knobs
        critical_knobs = ['tile_color', 'disable', 'hide_input']
        for knob_name in critical_knobs:
            knob = node.knob(knob_name)
            if knob:
                try:
                    signature_parts.append(f"{knob_name}:{knob.value()}")
                except:
                    pass
        
        return "|".join(signature_parts)

# Helper functions
def delete_nodes(nodes: List['nuke.Node'] = None, **kwargs) -> Dict[str, Any]:
    """Helper function to delete nodes"""
    deleter = NodeDeleter()
    return deleter.delete_nodes(nodes, **kwargs)

def delete_orphaned_nodes(nodes: List['nuke.Node'] = None) -> Dict[str, Any]:
    """Helper function to delete orphaned nodes"""
    deleter = NodeDeleter()
    return deleter.delete_orphaned_nodes(nodes)

def delete_by_type(node_classes: List[str], **kwargs) -> Dict[str, Any]:
    """Helper function to delete nodes by type"""
    deleter = NodeDeleter()
    return deleter.delete_by_type(node_classes, **kwargs)
