"""
Token Manager for Kite Connect
==============================

Manages Kite access token with file-based storage and automatic reloading.
Supports updating token without service restart.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from common.time_utils import now_ist_naive
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

        # Determine token file path (prefer passed path; default project root for backward compat)
        if token_file is None:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            token_file = project_root / "kite_token.json"
        self.token_file = Path(token_file).expanduser()
        self.token_data: Optional[Dict[str, Any]] = None
        self.observer: Optional[Observer] = None
        self.callbacks: list[Callable[[str], None]] = []

        # Ensure directory exists; create token file with template if not present
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.token_file.exists():
            self._create_template_token_file()
        self.logger.info(f"Token Manager initialized with file: {self.token_file}")

    def _create_template_token_file(self) -> None:
        """Create token file with empty template when not present (no file transfer)."""
        template = {
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "user_id": "",
            "user_name": "",
            "updated_at": now_ist_naive().isoformat(),
        }
        try:
            with open(self.token_file, "w") as f:
                json.dump(template, f, indent=2)
            self.logger.info(f"Created token template at {self.token_file}")
        except Exception as e:
            self.logger.error(f"Failed to create token template: {e}", exc_info=True)

    def load_token(self) -> Optional[str]:
        """
        Load access token from file. Also loads api_key and api_secret if present.

        Returns:
            Access token string if found, None otherwise
        """
        try:
            if not self.token_file.exists():
                self.logger.warning(f"Token file not found: {self.token_file}")
                return None

            with open(self.token_file, "r") as f:
                data = json.load(f)

            if isinstance(data, dict):
                token = data.get("access_token") or data.get("token")
                self.token_data = data
            elif isinstance(data, str):
                token = data
                self.token_data = {"access_token": token}
            else:
                self.logger.error(f"Invalid token file format: {self.token_file}")
                return None

            if token:
                self.logger.info(f"Token loaded from {self.token_file}")
            else:
                self.logger.warning("Token file exists but no access_token found")

            return token

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in token file: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading token from file: {e}", exc_info=True)
            return None

    def load_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Load api_key, api_secret, access_token from token file.
        All Kite credentials live in this file (not env).
        """
        self.load_token()
        return self.token_data

    def save_token(
        self,
        access_token: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        **kwargs,
    ) -> bool:
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
            # Preserve api_key and api_secret when updating token
            existing = self.token_data or {}
            if not existing and self.token_file.exists():
                try:
                    with open(self.token_file, "r") as f:
                        existing = json.load(f)
                except Exception:
                    pass

            token_data = {
                "access_token": access_token,
                "updated_at": now_ist_naive().isoformat(),
                "api_key": existing.get("api_key", ""),
                "api_secret": existing.get("api_secret", ""),
            }
            if user_id:
                token_data["user_id"] = user_id
            if user_name:
                token_data["user_name"] = user_name
            token_data.update(kwargs)

            with open(self.token_file, "w") as f:
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
