"""
Validation utilities for Nuke scripts and nodes
"""

import re
from typing import Dict, List, Optional, Any, Tuple
import nuke

from ..core.logging_utils import get_logger
from ..core.constants import *
from ..graph.traversal import GraphTraversal
from ..graph.connections import ConnectionManager

logger = get_logger(__name__)

class ValidationManager:
    """Validation utilities for Nuke scripts"""
    
    def __init__(self):
        self.traversal = GraphTraversal()
        self.connections = ConnectionManager()
    
    def validate_nuke_script(self) -> Dict[str, Any]:
        """
        Validate entire Nuke script
        
        Returns:
            Validation results
        """
        with TimerContext("validate_nuke_script", logger):
            try:
                results = {
                    'valid': True,
                    'warnings': [],
                    'errors': [],
                    'statistics': {},
                    'checks': {}
                }
                
                # Run various checks
                results['checks']['nodes'] = self._validate_nodes()
                results['checks']['connections'] = self._validate_connections()
                results['checks']['write_nodes'] = self._validate_write_nodes()
                results['checks']['performance'] = self._validate_performance()
                results['checks']['naming'] = self._validate_naming()
                
                # Collect results
                for check_name, check_result in results['checks'].items():
                    if 'errors' in check_result:
                        results['errors'].extend(check_result['errors'])
                    if 'warnings' in check_result:
                        results['warnings'].extend(check_result['warnings'])
                
                # Update overall validity
                results['valid'] = len(results['errors']) == 0
                
                # Add statistics
                results['statistics'] = {
                    'total_nodes': len(nuke.allNodes()),
                    'total_errors': len(results['errors']),
                    'total_warnings': len(results['warnings'])
                }
                
                logger.info(f"Script validation: {len(results['errors'])} errors, {len(results['warnings'])} warnings")
                return results
                
            except Exception as e:
                logger.error(f"Failed to validate script: {e}")
                return {'valid': False, 'errors': [str(e)]}
    
    def _validate_nodes(self) -> Dict[str, Any]:
        """Validate all nodes in script"""
        nodes = nuke.allNodes()
        errors = []
        warnings = []
        
        for node in nodes:
            # Check for invalid node names
            if not self._is_valid_node_name(node.name()):
                errors.append(f"Invalid node name: {node.name()}")
            
            # Check for duplicate names
            if self._has_duplicate_name(node, nodes):
                warnings.append(f"Duplicate node name: {node.name()}")
            
            # Check for missing plugins
            if self._is_missing_plugin(node):
                errors.append(f"Missing plugin for node: {node.name()}")
            
            # Check for disabled nodes with connections
            disable_knob = node.knob('disable')
            if disable_knob and disable_knob.value():
                if node.dependent() or any(node.input(i) for i in range(node.inputs())):
                    warnings.append(f"Disabled node has connections: {node.name()}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_connections(self) -> Dict[str, Any]:
        """Validate node connections"""
        nodes = nuke.allNodes()
        errors = []
        warnings = []
        
        # Check for cycles
        cycles = self.traversal.find_cycles(nodes)
        if cycles:
            for cycle in cycles:
                cycle_names = [n.name() for n in cycle]
                errors.append(f"Cycle detected: {' -> '.join(cycle_names)}")
        
        # Check for disconnected nodes
        for node in nodes:
            has_inputs = any(node.input(i) for i in range(node.inputs()))
            has_outputs = len(node.dependent()) > 0
            
            if not has_inputs and not has_outputs:
                warnings.append(f"Disconnected node: {node.name()}")
            
            # Check for mismatched connections
            for i in range(node.inputs()):
                input_node = node.input(i)
                if input_node:
                    # Check if output exists on input node
                    if node not in input_node.dependent():
                        errors.append(f"Connection mismatch: {input_node.name()} -> {node.name()}[{i}]")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_write_nodes(self) -> Dict[str, Any]:
        """Validate write nodes"""
        write_nodes = nuke.allNodes('Write')
        errors = []
        warnings = []
        
        for node in write_nodes:
            # Check filepath
            file_knob = node.knob('file')
            if not file_knob or not file_knob.value():
                errors.append(f"Write node has no filepath: {node.name()}")
                continue
            
            filepath = file_knob.value()
            
            # Check for placeholder patterns
            if '%' not in filepath and '#' not in filepath:
                warnings.append(f"Write node may be missing frame padding: {node.name()}")
            
            # Check directory exists
            try:
                import os
                dir_path = os.path.dirname(filepath.replace('%04d', '0001').replace('####', '0001'))
                if dir_path and not os.path.exists(dir_path):
                    warnings.append(f"Output directory doesn't exist: {dir_path}")
            except:
                pass
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_performance(self) -> Dict[str, Any]:
        """Validate performance issues"""
        nodes = nuke.allNodes()
        warnings = []
        
        # Check for too many nodes
        if len(nodes) > 500:
            warnings.append(f"Large number of nodes: {len(nodes)}")
        
        # Check for complex trees
        for node in nodes:
            dependents = len(node.dependent())
            if dependents > 10:
                warnings.append(f"Node has many outputs: {node.name()} ({dependents} outputs)")
            
            # Check for deep dependency chains
            depth = self._get_dependency_depth(node)
            if depth > 20:
                warnings.append(f"Deep dependency chain: {node.name()} (depth {depth})")
        
        return {'warnings': warnings}
    
    def _validate_naming(self) -> Dict[str, Any]:
        """Validate node naming conventions"""
        nodes = nuke.allNodes()
        warnings = []
        
        naming_patterns = {
            'Read': r'^Read',
            'Write': r'^Write',
            'Grade': r'^Grade',
            'Transform': r'^Transform',
            'Merge': r'^Merge'
        }
        
        for node in nodes:
            node_class = node.Class()
            node_name = node.name()
            
            if node_class in naming_patterns:
                pattern = naming_patterns[node_class]
                if not re.match(pattern, node_name):
                    warnings.append(f"Non-standard naming: {node.name()} (should match {pattern})")
        
        return {'warnings': warnings}
    
    def validate_node(self, node: 'nuke.Node') -> Dict[str, Any]:
        """
        Validate a single node
        
        Args:
            node: Node to validate
            
        Returns:
            Validation results
        """
        try:
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'node_info': {
                    'name': node.name(),
                    'class': node.Class(),
                    'inputs': node.inputs(),
                    'outputs': len(node.dependent())
                }
            }
            
            # Check node name
            if not self._is_valid_node_name(node.name()):
                results['errors'].append("Invalid node name")
                results['valid'] = False
            
            # Check for missing plugin
            if self._is_missing_plugin(node):
                results['errors'].append("Missing plugin")
                results['valid'] = False
            
            # Check knob values
            knob_errors = self._validate_knobs(node)
            results['errors'].extend(knob_errors)
            if knob_errors:
                results['valid'] = False
            
            # Check connections
            connection_warnings = self._validate_node_connections(node)
            results['warnings'].extend(connection_warnings)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to validate node: {e}")
            return {'valid': False, 'errors': [str(e)]}
    
    def _validate_knobs(self, node: 'nuke.Node') -> List[str]:
        """Validate node knobs"""
        errors = []
        
        try:
            for knob_name in node.knobs():
                knob = node.knob(knob_name)
                if knob:
                    # Check for expression errors
                    if knob.hasExpression():
                        try:
                            # Try to evaluate expression
                            knob.value()
                        except Exception as e:
                            errors.append(f"Knob '{knob_name}' has invalid expression: {str(e)}")
                    
                    # Check for out-of-range values
                    if knob.Class() in ['Int_Knob', 'Float_Knob']:
                        try:
                            value = knob.value()
                            if hasattr(knob, 'minimum') and hasattr(knob, 'maximum'):
                                min_val = knob.minimum()
                                max_val = knob.maximum()
                                if value < min_val or value > max_val:
                                    errors.append(f"Knob '{knob_name}' value {value} out of range [{min_val}, {max_val}]")
                        except:
                            pass
        except:
            pass
        
        return errors
    
    def _validate_node_connections(self, node: 'nuke.Node') -> List[str]:
        """Validate node connections"""
        warnings = []
        
        # Check for unused inputs
        for i in range(node.inputs()):
            if not node.input(i):
                warnings.append(f"Unused input {i}")
        
        # Check for disconnected outputs
        if not node.dependent():
            warnings.append("No outputs connected")
        
        return warnings
    
    def _is_valid_node_name(self, name: str) -> bool:
        """Check if node name is valid"""
        # Basic validation
        if not name or len(name) > 100:
            return False
        
        # Check for invalid characters
        invalid_chars = r'[\\/:*?"<>|]'
        if re.search(invalid_chars, name):
            return False
        
        return True
    
    def _has_duplicate_name(self, node: 'nuke.Node', all_nodes: List['nuke.Node']) -> bool:
        """Check if node has duplicate name"""
        name = node.name()
        count = sum(1 for n in all_nodes if n.name() == name)
        return count > 1
    
    def _is_missing_plugin(self, node: 'nuke.Node') -> bool:
        """Check if node is missing a plugin"""
        # This is a simplified check
        # In practice, you'd check if the node class is available
        try:
            # Try to access a property
            _ = node.Class()
            return False
        except:
            return True
    
    def _get_dependency_depth(self, node: 'nuke.Node') -> int:
        """Get maximum dependency depth"""
        max_depth = 0
        
        def traverse(current, depth, visited):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            for i in range(current.inputs()):
                input_node = current.input(i)
                if input_node and input_node not in visited:
                    visited.add(input_node)
                    traverse(input_node, depth + 1, visited)
        
        traverse(node, 0, set([node]))
        return max_depth

# Helper functions
def validate_nuke_script() -> Dict[str, Any]:
    """Helper function to validate Nuke script"""
    manager = ValidationManager()
    return manager.validate_nuke_script()

def validate_node(node: 'nuke.Node') -> Dict[str, Any]:
    """Helper function to validate a node"""
    manager = ValidationManager()
    return manager.validate_node(node)