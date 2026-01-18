"""
Node query and information utilities
"""

import re
from typing import Dict, List, Tuple, Optional, Any, Set
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.constants import *
from ..data.cache import cached_function
from ..graph.traversal import GraphTraversal

logger = get_logger(__name__)

class NodeQuery:
    """Advanced node query and information utilities"""
    
    def __init__(self):
        self.traversal = GraphTraversal()
    
    @cached_function(ttl=60)
    def get_node_info(self, node: 'nuke.Node') -> Dict[str, Any]:
        """
        Get comprehensive information about a node
        
        Args:
            node: Node to query
            
        Returns:
            Dictionary with node information
        """
        try:
            info = {
                'basic': {
                    'name': node.name(),
                    'class': node.Class(),
                    'full_name': node.fullName(),
                    'position': (node.xpos(), node.ypos()),
                    'size': (node.screenWidth(), node.screenHeight()),
                    'selected': node.isSelected(),
                    'modified': node.modified()
                },
                'connections': {
                    'num_inputs': node.inputs(),
                    'num_outputs': len(node.dependent()),
                    'inputs': [],
                    'outputs': []
                },
                'knobs': {},
                'metadata': {},
                'performance': {}
            }
            
            # Get input connections
            for i in range(node.inputs()):
                input_node = node.input(i)
                if input_node:
                    info['connections']['inputs'].append({
                        'index': i,
                        'node': input_node.name(),
                        'class': input_node.Class()
                    })
            
            # Get output connections
            for i, dep in enumerate(node.dependent()):
                info['connections']['outputs'].append({
                    'index': i,
                    'node': dep.name(),
                    'class': dep.Class()
                })
            
            # Get knob information
            for knob_name in node.knobs():
                knob = node.knob(knob_name)
                if knob:
                    try:
                        knob_info = {
                            'type': knob.Class(),
                            'value': knob.value(),
                            'label': knob.label(),
                            'visible': knob.visible(),
                            'enabled': knob.enabled(),
                            'is_animated': self._is_knob_animated(knob),
                            'has_expression': knob.hasExpression()
                        }
                        info['knobs'][knob_name] = knob_info
                    except:
                        pass
            
            # Get metadata
            tile_color = node.knob('tile_color')
            if tile_color:
                info['metadata']['tile_color'] = tile_color.value()
            
            disable_knob = node.knob('disable')
            if disable_knob:
                info['metadata']['disabled'] = disable_knob.value()
            
            # Estimate performance impact
            info['performance'] = self._estimate_node_performance(node)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get node info for {node.name()}: {e}")
            return {}
    
    def find_nodes(self, filters: Dict[str, Any] = None,
                  search_all: bool = True) -> List['nuke.Node']:
        """
        Find nodes matching multiple criteria
        
        Args:
            filters: Dictionary of filter criteria
            search_all: Search all nodes (False = selected nodes only)
            
        Returns:
            List of matching nodes
        """
        try:
            # Get nodes to search
            if search_all:
                nodes = nuke.allNodes()
            else:
                nodes = nuke.selectedNodes()
            
            if not filters:
                return nodes
            
            filtered_nodes = []
            
            for node in nodes:
                if self._node_matches_filters(node, filters):
                    filtered_nodes.append(node)
            
            return filtered_nodes
            
        except Exception as e:
            logger.error(f"Failed to find nodes: {e}")
            return []
    
    def find_nodes_by_name(self, pattern: str,
                          use_regex: bool = False,
                          case_sensitive: bool = False) -> List['nuke.Node']:
        """
        Find nodes by name pattern
        
        Args:
            pattern: Search pattern
            use_regex: Use regex pattern matching
            case_sensitive: Case-sensitive matching
            
        Returns:
            List of matching nodes
        """
        try:
            nodes = nuke.allNodes()
            matching_nodes = []
            
            for node in nodes:
                node_name = node.name()
                
                if use_regex:
                    if re.search(pattern, node_name):
                        matching_nodes.append(node)
                else:
                    if not case_sensitive:
                        if pattern.lower() in node_name.lower():
                            matching_nodes.append(node)
                    else:
                        if pattern in node_name:
                            matching_nodes.append(node)
            
            return matching_nodes
            
        except Exception as e:
            logger.error(f"Failed to find nodes by name: {e}")
            return []
    
    def find_nodes_by_class(self, node_classes: List[str],
                          exact_match: bool = True) -> List['nuke.Node']:
        """
        Find nodes by class
        
        Args:
            node_classes: List of node classes to find
            exact_match: Require exact class match
            
        Returns:
            List of matching nodes
        """
        try:
            nodes = nuke.allNodes()
            matching_nodes = []
            
            for node in nodes:
                node_class = node.Class()
                
                if exact_match:
                    if node_class in node_classes:
                        matching_nodes.append(node)
                else:
                    node_class_lower = node_class.lower()
                    for target_class in node_classes:
                        if target_class.lower() in node_class_lower:
                            matching_nodes.append(node)
                            break
            
            return matching_nodes
            
        except Exception as e:
            logger.error(f"Failed to find nodes by class: {e}")
            return []
    
    def find_nodes_by_knob_value(self, knob_name: str,
                                knob_value: Any,
                                comparison: str = 'equals') -> List['nuke.Node']:
        """
        Find nodes by knob value
        
        Args:
            knob_name: Knob name to check
            knob_value: Value to compare against
            comparison: 'equals', 'not_equals', 'contains', 'greater', 'less'
            
        Returns:
            List of matching nodes
        """
        try:
            nodes = nuke.allNodes()
            matching_nodes = []
            
            for node in nodes:
                knob = node.knob(knob_name)
                if not knob:
                    continue
                
                try:
                    current_value = knob.value()
                    
                    if comparison == 'equals':
                        if current_value == knob_value:
                            matching_nodes.append(node)
                    elif comparison == 'not_equals':
                        if current_value != knob_value:
                            matching_nodes.append(node)
                    elif comparison == 'contains':
                        if str(knob_value) in str(current_value):
                            matching_nodes.append(node)
                    elif comparison == 'greater':
                        if current_value > knob_value:
                            matching_nodes.append(node)
                    elif comparison == 'less':
                        if current_value < knob_value:
                            matching_nodes.append(node)
                            
                except:
                    continue
            
            return matching_nodes
            
        except Exception as e:
            logger.error(f"Failed to find nodes by knob value: {e}")
            return []
    
    def get_script_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive script statistics
        
        Returns:
            Dictionary with script statistics
        """
        try:
            nodes = nuke.allNodes()
            
            stats = {
                'total_nodes': len(nodes),
                'node_counts': defaultdict(int),
                'connection_stats': {
                    'total_connections': 0,
                    'average_connections': 0,
                    'max_connections': 0
                },
                'node_types': {},
                'performance_estimate': self._estimate_script_performance(nodes)
            }
            
            # Count nodes by class
            for node in nodes:
                node_class = node.Class()
                stats['node_counts'][node_class] += 1
            
            # Calculate connection statistics
            total_connections = 0
            max_connections = 0
            
            for node in nodes:
                num_inputs = sum(1 for i in range(node.inputs()) if node.input(i))
                num_outputs = len(node.dependent())
                total_connections += num_inputs + num_outputs
                max_connections = max(max_connections, num_inputs + num_outputs)
            
            stats['connection_stats']['total_connections'] = total_connections
            stats['connection_stats']['max_connections'] = max_connections
            
            if nodes:
                stats['connection_stats']['average_connections'] = total_connections / len(nodes)
            
            # Categorize nodes by type
            stats['node_types'] = self._categorize_nodes(nodes)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get script statistics: {e}")
            return {}
    
    def get_node_hierarchy(self, start_node: 'nuke.Node' = None) -> Dict[str, Any]:
        """
        Get node hierarchy starting from a node
        
        Args:
            start_node: Starting node (None for root nodes)
            
        Returns:
            Nested hierarchy dictionary
        """
        try:
            if start_node is None:
                # Find root nodes (no inputs)
                root_nodes = [
                    n for n in nuke.allNodes() 
                    if all(n.input(i) is None for i in range(n.inputs()))
                ]
                
                if not root_nodes:
                    return {}
                
                # Build hierarchy from first root node
                start_node = root_nodes[0]
            
            hierarchy = {
                'node': start_node.name(),
                'class': start_node.Class(),
                'children': []
            }
            
            # Get dependents as children
            for dependent in start_node.dependent():
                child_hierarchy = self.get_node_hierarchy(dependent)
                if child_hierarchy:
                    hierarchy['children'].append(child_hierarchy)
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"Failed to get node hierarchy: {e}")
            return {}
    
    # def compare_nodes(self, node1: 'nuke.Node', 
    #                  node2: 'nuke.Node') -> Dict[str, Any]:
    #     """
    #     Compare two nodes
        
    #     Args:
    #         node1: First node
    #         node2: Second node
            
    #     Returns:
    #         Dictionary with comparison results
    #     """
    #     try:
    #         info1 = self.get_node_info(node1)
    #         info2 = self.get_node_info(node2)
            
    #         comparison = {
    #             'same_class': node1.Class() == node2.Class(),
    #             'same_position': (
    #                 node1.xpos() == node2.xpos() and 
    #                 node1.ypos() == node2.ypos()
    #             ),
    #             'same_color': info1.get('metadata', {}).get('tile_color') == 
    #                          info2.get('metadata', {}).get('tile

