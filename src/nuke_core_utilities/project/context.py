"""
Project context and session management
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import nuke

from ..core.logging_utils import get_logger, TimerContext
from ..core.env import get_env
from ..core.constants import *

logger = get_logger(__name__)

class ProjectContext:
    """Project context and session management"""
    
    def __init__(self):
        self.env = get_env()
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        self.context_data = {}
        self._load_context()
    
    def _load_context(self):
        """Load project context from environment"""
        self.context_data = {
            'project': self.env.get_env('PROJECT_ROOT'),
            'show': self.env.get_env('SHOW'),
            'shot': self.env.get_env('SHOT'),
            'task': self.env.get_env('TASK'),
            'dept': self.env.get_env('DEPT'),
            'user': self.env.get_user_info().get('username'),
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'nuke_version': self.env.get_nuke_version(),
            'script_path': nuke.root().name() if hasattr(nuke, 'root') else None
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Get current project context"""
        return self.context_data.copy()
    
    def set_context_value(self, key: str, value: Any):
        """Set a context value"""
        self.context_data[key] = value
    
    def update_from_script(self):
        """Update context from current script"""
        try:
            script_path = nuke.root().name()
            if script_path:
                self.context_data['script_path'] = script_path
                self.context_data['script_name'] = Path(script_path).name
                self.context_data['script_dir'] = str(Path(script_path).parent)
                
                # Try to extract show/shot from script path
                self._extract_show_shot_from_path(script_path)
        except Exception as e:
            logger.warning(f"Failed to update context from script: {e}")
    
    def _extract_show_shot_from_path(self, path: str):
        """Extract show and shot from file path"""
        try:
            path_lower = path.lower()
            
            # Common patterns
            patterns = [
                r'/([a-z]+)_([a-z0-9]+)/',
                r'/([a-z]+)/([a-z0-9]+)/',
                r'_([a-z]+)_([a-z0-9]+)_'
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, path_lower)
                if match:
                    if not self.context_data.get('show'):
                        self.context_data['show'] = match.group(1).upper()
                    if not self.context_data.get('shot'):
                        self.context_data['shot'] = match.group(2).upper()
                    break
        except:
            pass
    
    def save_context(self, filepath: str = None) -> bool:
        """Save context to file"""
        try:
            if filepath is None:
                context_dir = Path(self.env.get_nuke_temp_dir()) / 'context'
                context_dir.mkdir(exist_ok=True)
                filepath = context_dir / f'context_{self.session_id}.json'
            
            self.context_data['save_time'] = datetime.now().isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(self.context_data, f, indent=2)
            
            logger.info(f"Saved project context to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    def load_context(self, filepath: str) -> bool:
        """Load context from file"""
        try:
            with open(filepath, 'r') as f:
                loaded_data = json.load(f)
            
            self.context_data.update(loaded_data)
            
            # Update environment variables
            for key in ['show', 'shot', 'task', 'dept']:
                if key in self.context_data:
                    self.env.set_env(key.upper(), self.context_data[key], persistent=True)
            
            logger.info(f"Loaded project context from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return False
    
    def create_context_report(self) -> str:
        """Create a context report"""
        report = []
        report.append("="*60)
        report.append("PROJECT CONTEXT REPORT")
        report.append("="*60)
        
        for key, value in sorted(self.context_data.items()):
            report.append(f"{key:20}: {value}")
        
        report.append("="*60)
        return "\n".join(report)
    
    def validate_context(self) -> Dict[str, Any]:
        """Validate current context"""
        warnings = []
        errors = []
        
        # Check required fields
        required = ['show', 'shot', 'task']
        for field in required:
            if not self.context_data.get(field):
                warnings.append(f"Missing required field: {field}")
        
        # Check script
        if not self.context_data.get('script_path'):
            warnings.append("No script loaded")
        
        # Check paths
        project_root = self.context_data.get('project')
        if project_root and not Path(project_root).exists():
            errors.append(f"Project root does not exist: {project_root}")
        
        return {
            'valid': len(errors) == 0,
            'warnings': warnings,
            'errors': errors,
            'context': self.context_data
        }

# Global context instance
_project_context = None

def get_project_context() -> ProjectContext:
    """Get global project context"""
    global _project_context
    if _project_context is None:
        _project_context = ProjectContext()
    return _project_context

def update_project_context():
    """Update project context from current state"""
    context = get_project_context()
    context.update_from_script()