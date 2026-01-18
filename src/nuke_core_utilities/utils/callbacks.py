"""
Callback management for Nuke events
"""

import sys
import traceback
from typing import Dict, List, Optional, Callable, Any
import nuke

from ..core.logging_utils import get_logger

logger = get_logger(__name__)

class CallbackManager:
    """Callback management for Nuke events"""
    
    def __init__(self):
        self.callbacks = {
            'onScriptLoad': [],
            'onScriptSave': [],
            'onScriptClose': [],
            'onCreate': [],
            'onDestroy': [],
            'onUserCreate': [],
            'onScriptLoadFailed': [],
            'onFilenameChanged': [],
            'onAutoSave': []
        }
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup Nuke callbacks"""
        try:
            # Clear existing callbacks
            nuke.removeOnScriptLoad(self._script_load_callback)
            nuke.removeOnScriptSave(self._script_save_callback)
            nuke.removeOnScriptClose(self._script_close_callback)
            nuke.removeOnCreate(self._create_callback)
            nuke.removeOnDestroy(self._destroy_callback)
            nuke.removeOnUserCreate(self._user_create_callback)
            
            # Add our callbacks
            nuke.addOnScriptLoad(self._script_load_callback)
            nuke.addOnScriptSave(self._script_save_callback)
            nuke.addOnScriptClose(self._script_close_callback)
            nuke.addOnCreate(self._create_callback)
            nuke.addOnDestroy(self._destroy_callback)
            nuke.addOnUserCreate(self._user_create_callback)
            
            logger.debug("Setup Nuke callbacks")
            
        except Exception as e:
            logger.error(f"Failed to setup callbacks: {e}")
    
    def add_callback(self, event: str, callback: Callable, 
                    priority: int = 0) -> bool:
        """
        Add a callback for an event
        
        Args:
            event: Event name
            callback: Callback function
            priority: Callback priority (higher = called first)
            
        Returns:
            Success status
        """
        try:
            if event not in self.callbacks:
                logger.error(f"Unknown event: {event}")
                return False
            
            # Add callback with priority
            self.callbacks[event].append({
                'function': callback,
                'priority': priority
            })
            
            # Sort by priority
            self.callbacks[event].sort(key=lambda x: x['priority'], reverse=True)
            
            logger.debug(f"Added callback for event '{event}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add callback: {e}")
            return False
    
    def remove_callback(self, event: str, callback: Callable) -> bool:
        """
        Remove a callback
        
        Args:
            event: Event name
            callback: Callback function to remove
            
        Returns:
            Success status
        """
        try:
            if event not in self.callbacks:
                return False
            
            # Find and remove callback
            for i, cb_info in enumerate(self.callbacks[event]):
                if cb_info['function'] == callback:
                    self.callbacks[event].pop(i)
                    logger.debug(f"Removed callback for event '{event}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove callback: {e}")
            return False
    
    def clear_callbacks(self, event: str = None):
        """
        Clear callbacks
        
        Args:
            event: Specific event (None for all events)
        """
        try:
            if event:
                if event in self.callbacks:
                    self.callbacks[event].clear()
                    logger.debug(f"Cleared callbacks for event '{event}'")
            else:
                for event_name in self.callbacks:
                    self.callbacks[event_name].clear()
                logger.debug("Cleared all callbacks")
                
        except Exception as e:
            logger.error(f"Failed to clear callbacks: {e}")
    
    def _execute_callbacks(self, event: str, *args, **kwargs):
        """Execute callbacks for an event"""
        try:
            if event not in self.callbacks:
                return
            
            for cb_info in self.callbacks[event]:
                try:
                    cb_info['function'](*args, **kwargs)
                except Exception as e:
                    logger.error(f"Callback error for event '{event}': {e}")
                    logger.error(traceback.format_exc())
                    
        except Exception as e:
            logger.error(f"Failed to execute callbacks: {e}")
    
    def _script_load_callback(self):
        """Callback for script load"""
        try:
            logger.info("Script loaded")
            self._execute_callbacks('onScriptLoad')
        except Exception as e:
            logger.error(f"Script load callback error: {e}")
    
    def _script_save_callback(self):
        """Callback for script save"""
        try:
            logger.info("Script saved")
            self._execute_callbacks('onScriptSave')
        except Exception as e:
            logger.error(f"Script save callback error: {e}")
    
    def _script_close_callback(self):
        """Callback for script close"""
        try:
            logger.info("Script closing")
            self._execute_callbacks('onScriptClose')
        except Exception as e:
            logger.error(f"Script close callback error: {e}")
    
    def _create_callback(self):
        """Callback for node creation"""
        try:
            self._execute_callbacks('onCreate')
        except Exception as e:
            logger.error(f"Create callback error: {e}")
    
    def _destroy_callback(self):
        """Callback for node destruction"""
        try:
            self._execute_callbacks('onDestroy')
        except Exception as e:
            logger.error(f"Destroy callback error: {e}")
    
    def _user_create_callback(self):
        """Callback for user node creation"""
        try:
            self._execute_callbacks('onUserCreate')
        except Exception as e:
            logger.error(f"User create callback error: {e}")
    
    def add_menu_callbacks(self):
        """Add callbacks for menu actions"""
        try:
            # Add callback for menu creation
            nuke.addOnCreate(self._menu_create_callback)
            logger.debug("Added menu callbacks")
        except Exception as e:
            logger.error(f"Failed to add menu callbacks: {e}")
    
    def _menu_create_callback(self):
        """Callback for menu creation"""
        try:
            # This is called when menus are created
            # You can modify menus here
            pass
        except Exception as e:
            logger.error(f"Menu create callback error: {e}")
    
    def add_timer_callback(self, interval: float, callback: Callable) -> bool:
        """
        Add a timer callback
        
        Args:
            interval: Interval in seconds
            callback: Callback function
            
        Returns:
            Success status
        """
        try:
            # Create timer
            timer_id = nuke.addUpdate(callback, interval)
            
            if timer_id:
                logger.debug(f"Added timer callback with interval {interval}s")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add timer callback: {e}")
            return False
    
    def remove_timer_callback(self, callback: Callable) -> bool:
        """
        Remove a timer callback
        
        Args:
            callback: Callback function to remove
            
        Returns:
            Success status
        """
        try:
            # Note: Nuke doesn't have a direct way to remove specific callbacks
            # This would need to be handled differently
            logger.warning("Timer callback removal not implemented")
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove timer callback: {e}")
            return False

# Global callback manager instance
_callback_manager = None

def get_callback_manager() -> CallbackManager:
    """Get global callback manager"""
    global _callback_manager
    if _callback_manager is None:
        _callback_manager = CallbackManager()
    return _callback_manager

def add_callback(event: str, callback: Callable, **kwargs) -> bool:
    """Helper function to add callback"""
    manager = get_callback_manager()
    return manager.add_callback(event, callback, **kwargs)

def remove_callback(event: str, callback: Callable) -> bool:
    """Helper function to remove callback"""
    manager = get_callback_manager()
    return manager.remove_callback(event, callback)

def clear_callbacks(event: str = None):
    """Helper function to clear callbacks"""
    manager = get_callback_manager()
    manager.clear_callbacks(event)