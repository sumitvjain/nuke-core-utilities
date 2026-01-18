"""
File read/write operations for Nuke scripts and data
"""

import json
import pickle
import yaml
import xml.etree.ElementTree as ET
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.env import get_env
from ..core.constants import EXT_NK, EXT_JSON, EXT_YAML, EXT_XML, EXT_TXT

logger = get_logger(__name__)

class NukeFileHandler:
    """Handler for Nuke file operations"""
    
    def __init__(self):
        self.env = get_env()
        self.backup_dir = Path(self.env.get_nuke_temp_dir()) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def read_nuke_script(self, filepath: str, 
                        load_all_formats: bool = False,
                        restore_views: bool = True) -> bool:
        """
        Read Nuke script with enhanced options
        
        Args:
            filepath: Path to .nk file
            load_all_formats: Load all read node file formats
            restore_views: Restore saved viewer states
            
        Returns:
            Success status
        """
        with TimerContext(f"read_nuke_script_{Path(filepath).name}", logger):
            try:
                # Backup current script if any
                if nuke.modified():
                    self._create_backup()
                
                # Clear current script
                nuke.scriptClear()
                
                # Load script
                nuke.scriptReadFile(filepath)
                
                # Load formats if requested
                if load_all_formats:
                    self._load_all_formats()
                
                # Restore views
                if restore_views:
                    self._restore_viewer_states()
                
                logger.info(f"Successfully loaded script: {filepath}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load script {filepath}: {e}")
                return False
    
    def write_nuke_script(self, filepath: str, 
                         compression: int = 0,
                         overwrite: bool = True,
                         backup: bool = True) -> bool:
        """
        Write Nuke script with enhanced options
        
        Args:
            filepath: Output path
            compression: Compression level (0-9)
            overwrite: Overwrite existing file
            backup: Create backup before overwriting
            
        Returns:
            Success status
        """
        with TimerContext(f"write_nuke_script_{Path(filepath).name}", logger):
            try:
                filepath = Path(filepath)
                
                # Check if file exists
                if filepath.exists():
                    if not overwrite:
                        logger.error(f"File exists and overwrite=False: {filepath}")
                        return False
                    
                    if backup:
                        self._backup_existing_file(filepath)
                
                # Ensure directory exists
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                # Save script
                nuke.scriptSave(str(filepath))
                
                # Apply compression if requested
                if compression > 0:
                    self._compress_nk_file(filepath, compression)
                
                logger.info(f"Successfully saved script: {filepath}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save script {filepath}: {e}")
                return False
    
    def export_node_preset(self, node: 'nuke.Node', filepath: str,
                          include_connections: bool = False) -> bool:
        """
        Export node as preset file
        
        Args:
            node: Node to export
            filepath: Output path
            include_connections: Include input connections
            
        Returns:
            Success status
        """
        try:
            # Create temp script with just this node
            temp_file = Path(tempfile.mktemp(suffix='.nk'))
            
            # Copy node to new script
            nuke.nodeCopy(str(temp_file))
            
            # Read back and add to dictionary
            with open(temp_file, 'r') as f:
                preset_data = {
                    'node_class': node.Class(),
                    'node_name': node.name(),
                    'knob_values': self._extract_knob_values(node),
                    'node_data': f.read()
                }
            
            if include_connections:
                preset_data['connections'] = self._extract_node_connections(node)
            
            # Save as JSON
            with open(filepath, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            # Cleanup
            temp_file.unlink()
            
            logger.info(f"Exported node preset: {node.name()} -> {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export node preset: {e}")
            return False
    
    def import_node_preset(self, filepath: str, 
                          parent_node: 'nuke.Node' = None) -> Optional['nuke.Node']:
        """
        Import node from preset file
        
        Args:
            filepath: Path to preset file
            parent_node: Parent node for Group/Backdrop
            
        Returns:
            Created node or None
        """
        try:
            with open(filepath, 'r') as f:
                preset_data = json.load(f)
            
            # Create temp script
            temp_file = Path(tempfile.mktemp(suffix='.nk'))
            with open(temp_file, 'w') as f:
                f.write(preset_data['node_data'])
            
            # Paste node
            nuke.nodePaste(str(temp_file))
            
            # Get the pasted node
            pasted_nodes = nuke.selectedNodes()
            if not pasted_nodes:
                return None
            
            node = pasted_nodes[0]
            
            # Apply knob values
            if 'knob_values' in preset_data:
                self._apply_knob_values(node, preset_data['knob_values'])
            
            # Position relative to parent
            if parent_node:
                self._position_relative_to_parent(node, parent_node)
            
            # Cleanup
            temp_file.unlink()
            
            logger.info(f"Imported node preset: {filepath} -> {node.name()}")
            return node
            
        except Exception as e:
            logger.error(f"Failed to import node preset: {e}")
            return None
    
    def export_selection(self, filepath: str,
                        include_backdrops: bool = True,
                        include_stickies: bool = True) -> bool:
        """
        Export selected nodes to file
        
        Args:
            filepath: Output path
            include_backdrops: Include backdrop nodes
            include_stickies: Include sticky notes
            
        Returns:
            Success status
        """
        try:
            selected_nodes = nuke.selectedNodes()
            
            if not selected_nodes:
                logger.warning("No nodes selected for export")
                return False
            
            # Filter nodes
            nodes_to_export = []
            for node in selected_nodes:
                if node.Class() == 'BackdropNode' and not include_backdrops:
                    continue
                if node.Class() == 'StickyNote' and not include_stickies:
                    continue
                nodes_to_export.append(node)
            
            # Select only nodes to export
            nuke.selectAll()
            nuke.invertSelection()
            for node in nodes_to_export:
                node.setSelected(True)
            
            # Export
            nuke.nodeCopy(str(filepath))
            
            # Restore selection
            nuke.selectAll()
            nuke.invertSelection()
            for node in selected_nodes:
                node.setSelected(True)
            
            logger.info(f"Exported {len(nodes_to_export)} nodes to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export selection: {e}")
            return False
    
    def import_nodes(self, filepath: str,
                    position: Tuple[int, int] = None,
                    connect_to_selected: bool = False) -> List['nuke.Node']:
        """
        Import nodes from file
        
        Args:
            filepath: Path to nodes file
            position: Position to place nodes
            connect_to_selected: Connect to selected nodes
            
        Returns:
            List of imported nodes
        """
        try:
            # Store current selection
            original_selection = nuke.selectedNodes()
            
            # Import nodes
            nuke.nodePaste(str(filepath))
            imported_nodes = nuke.selectedNodes()
            
            # Position nodes
            if position:
                self._position_nodes(imported_nodes, position)
            
            # Connect to selected nodes if requested
            if connect_to_selected and original_selection:
                self._connect_imported_nodes(imported_nodes, original_selection)
            
            logger.info(f"Imported {len(imported_nodes)} nodes from {filepath}")
            return imported_nodes
            
        except Exception as e:
            logger.error(f"Failed to import nodes: {e}")
            return []
    
    def read_json(self, filepath: str) -> Optional[Dict]:
        """Read JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read JSON {filepath}: {e}")
            return None
    
    def write_json(self, filepath: str, data: Dict, indent: int = 2) -> bool:
        """Write JSON file"""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=indent)
            
            return True
        except Exception as e:
            logger.error(f"Failed to write JSON {filepath}: {e}")
            return False
    
    def read_yaml(self, filepath: str) -> Optional[Dict]:
        """Read YAML file"""
        try:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to read YAML {filepath}: {e}")
            return None
    
    def write_yaml(self, filepath: str, data: Dict) -> bool:
        """Write YAML file"""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to write YAML {filepath}: {e}")
            return False
    
    def read_xml(self, filepath: str) -> Optional[ET.Element]:
        """Read XML file"""
        try:
            return ET.parse(filepath).getroot()
        except Exception as e:
            logger.error(f"Failed to read XML {filepath}: {e}")
            return None
    
    def write_xml(self, filepath: str, root: ET.Element) -> bool:
        """Write XML file"""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
            
            return True
        except Exception as e:
            logger.error(f"Failed to write XML {filepath}: {e}")
            return False
    
    def _create_backup(self):
        """Create backup of current script"""
        try:
            script_name = nuke.root().name() or 'unsaved'
            backup_name = f"{Path(script_name).stem}_{int(time.time())}.nk"
            backup_path = self.backup_dir / backup_name
            
            nuke.scriptSave(str(backup_path))
            logger.debug(f"Created backup: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _backup_existing_file(self, filepath: Path):
        """Backup existing file before overwriting"""
        try:
            backup_name = f"{filepath.stem}_backup_{int(time.time())}{filepath.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(filepath, backup_path)
            logger.debug(f"Backed up existing file: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to backup existing file: {e}")
    
    def _load_all_formats(self):
        """Load all read node file formats"""
        try:
            for node in nuke.allNodes('Read'):
                try:
                    node['reload'].execute()
                except:
                    pass
        except Exception as e:
            logger.warning(f"Failed to load all formats: {e}")
    
    def _restore_viewer_states(self):
        """Restore viewer states"""
        try:
            for viewer in nuke.allNodes('Viewer'):
                viewer['frame'].setValue(nuke.frame())
        except Exception as e:
            logger.warning(f"Failed to restore viewer states: {e}")
    
    def _compress_nk_file(self, filepath: Path, level: int):
        """Compress .nk file using zip"""
        try:
            zip_path = filepath.with_suffix('.nkz')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(filepath, filepath.name)
            
            # Replace original with compressed version
            filepath.unlink()
            logger.debug(f"Compressed script: {filepath} -> {zip_path}")
            
        except Exception as e:
            logger.warning(f"Failed to compress file: {e}")
    
    def _extract_knob_values(self, node: 'nuke.Node') -> Dict:
        """Extract knob values from node"""
        knob_values = {}
        for knob_name in node.knobs():
            knob = node[knob_name]
            if knob and knob.visible():
                try:
                    knob_values[knob_name] = knob.value()
                except:
                    pass
        return knob_values
    
    def _apply_knob_values(self, node: 'nuke.Node', knob_values: Dict):
        """Apply knob values to node"""
        for knob_name, value in knob_values.items():
            knob = node.knob(knob_name)
            if knob:
                try:
                    knob.setValue(value)
                except:
                    pass
    
    def _extract_node_connections(self, node: 'nuke.Node') -> Dict:
        """Extract node connections"""
        connections = {}
        for i in range(node.inputs()):
            input_node = node.input(i)
            if input_node:
                connections[f'input_{i}'] = input_node.name()
        return connections
    
    def _position_relative_to_parent(self, node: 'nuke.Node', parent: 'nuke.Node'):
        """Position node relative to parent"""
        try:
            parent_x, parent_y = parent.xpos(), parent.ypos()
            parent_w, parent_h = parent.screenWidth(), parent.screenHeight()
            
            node_x = parent_x + parent_w + 50
            node_y = parent_y
            
            node.setXpos(node_x)
            node.setYpos(node_y)
        except:
            pass
    
    def _position_nodes(self, nodes: List['nuke.Node'], position: Tuple[int, int]):
        """Position nodes at specified location"""
        if not nodes:
            return
        
        min_x = min(node.xpos() for node in nodes)
        min_y = min(node.ypos() for node in nodes)
        
        offset_x = position[0] - min_x
        offset_y = position[1] - min_y
        
        for node in nodes:
            node.setXpos(node.xpos() + offset_x)
            node.setYpos(node.ypos() + offset_y)
    
    def _connect_imported_nodes(self, imported: List['nuke.Node'], 
                               original: List['nuke.Node']):
        """Connect imported nodes to original selection"""
        try:
            # Connect first output of last original to first input of first imported
            if original and imported:
                last_original = original[-1]
                first_imported = imported[0]
                
                if last_original.outputs() > 0 and first_imported.inputs() > 0:
                    first_imported.setInput(0, last_original)
        except:
            pass

# Helper functions
def read_nuke_script(filepath: str, **kwargs) -> bool:
    """Helper function to read Nuke script"""
    handler = NukeFileHandler()
    return handler.read_nuke_script(filepath, **kwargs)

def write_nuke_script(filepath: str, **kwargs) -> bool:
    """Helper function to write Nuke script"""
    handler = NukeFileHandler()
    return handler.write_nuke_script(filepath, **kwargs)

def export_selection(filepath: str, **kwargs) -> bool:
    """Helper function to export selection"""
    handler = NukeFileHandler()
    return handler.export_selection(filepath, **kwargs)

def import_nodes(filepath: str, **kwargs) -> List['nuke.Node']:
    """Helper function to import nodes"""
    handler = NukeFileHandler()
    return handler.import_nodes(filepath, **kwargs)