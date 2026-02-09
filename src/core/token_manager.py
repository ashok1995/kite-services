"""
Token Manager for Kite Connect
==============================

Manages Kite access token with file-based storage and automatic reloading.
Supports updating token without service restart.
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.logging_config import get_logger


class TokenFileHandler(FileSystemEventHandler):
    """File system event handler for token file changes."""
    
    def __init__(self, callback: Callable[[], None]):
        self.callback = callback
        self.logger = get_logger(__name__)
    
    def on_modified(self, event):
        """Handle file modification event."""
        if not event.is_directory:
            self.logger.info(f"Token file modified: {event.src_path}")
            # Small delay to ensure file write is complete
            asyncio.create_task(self._delayed_callback())
    
    async def _delayed_callback(self):
        """Delayed callback to ensure file is fully written."""
        await asyncio.sleep(0.5)
        self.callback()


class TokenManager:
    """
    Manages Kite access token with file watching and automatic reloading.
    
    Features:
    - Reads token from file
    - Watches file for changes
    - Automatically reloads token when file is updated
    - Provides callback mechanism for token updates
    """
    
    def __init__(self, token_file: Optional[Path] = None):
        """
        Initialize Token Manager.
        
        Args:
            token_file: Path to token file. Defaults to 'kite_token.json' in project root.
        """
        self.logger = get_logger(__name__)
        
        # Determine token file path
        if token_file is None:
            # Default to project root / kite_token.json
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent  # Go up from src/core/
            token_file = project_root / "kite_token.json"
        
        self.token_file = Path(token_file)
        self.token_data: Optional[Dict[str, Any]] = None
        self.observer: Optional[Observer] = None
        self.callbacks: list[Callable[[str], None]] = []
        
        # Ensure token file directory exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Token Manager initialized with file: {self.token_file}")
    
    def load_token(self) -> Optional[str]:
        """
        Load access token from file.
        
        Returns:
            Access token string if found, None otherwise
        """
        try:
            if not self.token_file.exists():
                self.logger.warning(f"Token file not found: {self.token_file}")
                return None
            
            with open(self.token_file, 'r') as f:
                data = json.load(f)
            
            # Support multiple formats
            if isinstance(data, dict):
                # Format: {"access_token": "...", "user_id": "...", ...}
                token = data.get("access_token") or data.get("token")
                self.token_data = data
            elif isinstance(data, str):
                # Format: Just the token string
                token = data
                self.token_data = {"access_token": token}
            else:
                self.logger.error(f"Invalid token file format: {self.token_file}")
                return None
            
            if token:
                self.logger.info(f"✅ Token loaded from {self.token_file}")
                # Log partial token for verification
                token_preview = f"{token[:10]}..." if len(token) > 10 else token
                self.logger.info(f"Token preview: {token_preview}")
            else:
                self.logger.warning("Token file exists but no access_token found")
            
            return token
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in token file: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading token from file: {e}", exc_info=True)
            return None
    
    def save_token(self, access_token: str, user_id: Optional[str] = None, 
                   user_name: Optional[str] = None, **kwargs) -> bool:
        """
        Save access token to file.
        
        Args:
            access_token: The access token to save
            user_id: Optional user ID
            user_name: Optional user name
            **kwargs: Additional metadata to save
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            token_data = {
                "access_token": access_token,
                "updated_at": datetime.now().isoformat(),
            }
            
            if user_id:
                token_data["user_id"] = user_id
            if user_name:
                token_data["user_name"] = user_name
            
            # Add any additional metadata
            token_data.update(kwargs)
            
            # Save to file
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            self.token_data = token_data
            self.logger.info(f"✅ Token saved to {self.token_file}")
            
            # Notify callbacks (they will be called when file watcher detects change)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving token to file: {e}", exc_info=True)
            return False
    
    def update_token(self, access_token: str, **metadata) -> bool:
        """
        Update access token (alias for save_token).
        
        Args:
            access_token: The new access token
            **metadata: Additional metadata
        
        Returns:
            True if updated successfully
        """
        return self.save_token(access_token, **metadata)
    
    def start_watching(self, callback: Optional[Callable[[str], None]] = None):
        """
        Start watching token file for changes.
        
        Args:
            callback: Optional callback function to call when token changes.
                     Callback receives the new access token as argument.
        """
        if callback:
            self.callbacks.append(callback)
        
        if self.observer and self.observer.is_alive():
            self.logger.warning("File watcher already running")
            return
        
        try:
            # Create file system event handler
            handler = TokenFileHandler(self._on_token_file_changed)
            
            # Create observer
            self.observer = Observer()
            self.observer.schedule(handler, str(self.token_file.parent), recursive=False)
            self.observer.start()
            
            self.logger.info(f"✅ Started watching token file: {self.token_file}")
            
        except Exception as e:
            self.logger.error(f"Error starting file watcher: {e}", exc_info=True)
    
    def stop_watching(self):
        """Stop watching token file."""
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.logger.info("✅ Stopped watching token file")
            except Exception as e:
                self.logger.error(f"Error stopping file watcher: {e}")
    
    def _on_token_file_changed(self):
        """Handle token file change event."""
        self.logger.info("Token file changed, reloading...")
        new_token = self.load_token()
        
        if new_token:
            # Notify all callbacks
            for callback in self.callbacks:
                try:
                    callback(new_token)
                except Exception as e:
                    self.logger.error(f"Error in token change callback: {e}", exc_info=True)
        else:
            self.logger.warning("Token file changed but failed to load new token")
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        Get token information.
        
        Returns:
            Dictionary with token metadata, or None if not loaded
        """
        return self.token_data
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_watching()
