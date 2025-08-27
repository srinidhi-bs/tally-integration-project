#!/usr/bin/env python3
"""
Application Settings Management for TallyPrime Integration Manager

This module provides comprehensive settings management with Qt6 integration,
including connection configurations, UI preferences, and application state.

Author: Srinidhi BS (Learning to code)  
Assistant: Claude (Anthropic)
Date: August 26, 2025
Framework: PySide6 (Qt6)
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

# Qt6 imports for settings persistence
from PySide6.QtCore import QSettings, QObject, Signal
from PySide6.QtWidgets import QApplication

# Local imports
from core.tally.connector import TallyConnectionConfig

# Set up logger for this module  
logger = logging.getLogger(__name__)


@dataclass
class UIPreferences:
    """
    Data class for UI preferences and layout settings
    Stores user interface customization options
    """
    # Window settings
    window_geometry: Dict[str, int] = None
    window_state: bytes = None
    window_maximized: bool = False
    
    # Panel settings  
    control_panel_visible: bool = True
    log_panel_visible: bool = True
    control_panel_width: int = 300
    log_panel_width: int = 400
    
    # Theme and appearance
    theme_name: str = "professional"
    font_family: str = "Segoe UI"
    font_size: int = 10
    
    # Logging preferences
    log_level: str = "INFO"
    log_max_lines: int = 1000
    log_auto_scroll: bool = True
    
    def __post_init__(self):
        """Initialize default values after dataclass creation"""
        if self.window_geometry is None:
            self.window_geometry = {
                'x': 100, 'y': 100, 
                'width': 1200, 'height': 800
            }


@dataclass  
class ApplicationSettings:
    """
    Main application settings container
    Combines all setting categories for easy management
    """
    # TallyPrime connection settings
    connection: TallyConnectionConfig = None
    
    # UI preferences
    ui_preferences: UIPreferences = None
    
    # Connection history
    connection_history: List[Dict[str, Any]] = None
    
    # Application behavior
    auto_connect_on_startup: bool = False
    check_for_updates: bool = True
    enable_connection_monitoring: bool = True
    monitoring_interval_seconds: int = 30
    
    # Data preferences
    default_export_format: str = "CSV"
    max_records_per_query: int = 1000
    
    def __post_init__(self):
        """Initialize default values after dataclass creation"""
        if self.connection is None:
            self.connection = TallyConnectionConfig()
        if self.ui_preferences is None:
            self.ui_preferences = UIPreferences()
        if self.connection_history is None:
            self.connection_history = []


class SettingsManager(QObject):
    """
    Professional settings manager with Qt6 integration
    
    This class provides comprehensive settings management including:
    - Persistent storage using QSettings
    - Signal-based notifications for settings changes  
    - Connection configuration management
    - UI preferences handling
    - Settings validation and error handling
    - Backup and restore functionality
    
    Features:
    - Qt6 QSettings integration for cross-platform storage
    - Signal emissions for real-time UI updates
    - JSON serialization for complex data structures
    - Settings validation and error recovery
    - Connection history management
    - Import/export functionality for settings backup
    
    Signals:
        settings_changed: Emitted when any setting is modified
        connection_config_changed: Emitted when connection settings change
        ui_preferences_changed: Emitted when UI preferences change
    """
    
    # Qt6 Signals for real-time settings updates
    settings_changed = Signal(str, object)  # setting_name, new_value
    connection_config_changed = Signal(TallyConnectionConfig) 
    ui_preferences_changed = Signal(UIPreferences)
    
    def __init__(self, organization: str = "SrinidhiBS", application: str = "TallyPrimeManager"):
        """
        Initialize settings manager with Qt6 QSettings
        
        Args:
            organization: Organization name for settings storage
            application: Application name for settings storage
        """
        super().__init__()
        
        # Initialize Qt6 settings storage
        self.qt_settings = QSettings(organization, application)
        
        # Current settings instance
        self._settings = ApplicationSettings()
        
        # Settings file paths for JSON backup
        self.settings_dir = Path.home() / ".tally_integration_manager"
        self.settings_file = self.settings_dir / "settings.json"
        self.backup_dir = self.settings_dir / "backups"
        
        # Ensure settings directory exists
        self.settings_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load existing settings
        self._load_settings()
        
        logger.info("SettingsManager initialized")
    
    @property
    def settings(self) -> ApplicationSettings:
        """Get current application settings"""
        return self._settings
    
    @property
    def connection_config(self) -> TallyConnectionConfig:
        """Get current TallyPrime connection configuration"""
        return self._settings.connection
    
    @property
    def ui_preferences(self) -> UIPreferences:
        """Get current UI preferences"""
        return self._settings.ui_preferences
    
    def _load_settings(self):
        """
        Load settings from Qt6 QSettings and JSON backup
        Combines both storage methods for robustness
        """
        try:
            # Load from QSettings (cross-platform registry/config files)
            self._load_from_qt_settings()
            
            # Also try to load from JSON file as backup
            # TEMPORARY: Disable JSON loading to test Qt settings
            # if self.settings_file.exists():
            #     self._load_from_json_file()
            
            logger.info("Settings loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self._apply_default_settings()
    
    def _load_from_qt_settings(self):
        """Load settings from Qt6 QSettings storage"""
        
        # Connection settings
        old_host = self._settings.connection.host
        self._settings.connection.host = self.qt_settings.value(
            "connection/host", self._settings.connection.host
        )
        if self._settings.connection.host != old_host:
            logger.info(f"Qt settings overrode host: {old_host} -> {self._settings.connection.host}")
        self._settings.connection.port = int(self.qt_settings.value(
            "connection/port", self._settings.connection.port
        ))
        self._settings.connection.timeout = int(self.qt_settings.value(
            "connection/timeout", self._settings.connection.timeout  
        ))
        self._settings.connection.retry_count = int(self.qt_settings.value(
            "connection/retry_count", self._settings.connection.retry_count
        ))
        
        # UI preferences
        self._settings.ui_preferences.theme_name = self.qt_settings.value(
            "ui/theme_name", self._settings.ui_preferences.theme_name
        )
        self._settings.ui_preferences.font_family = self.qt_settings.value(
            "ui/font_family", self._settings.ui_preferences.font_family
        )
        self._settings.ui_preferences.font_size = int(self.qt_settings.value(
            "ui/font_size", self._settings.ui_preferences.font_size
        ))
        
        # Window geometry
        geometry = self.qt_settings.value("window/geometry")
        if geometry:
            self._settings.ui_preferences.window_geometry = {
                'x': geometry.x(), 'y': geometry.y(),
                'width': geometry.width(), 'height': geometry.height()
            }
        
        # Window state
        window_state = self.qt_settings.value("window/state")
        if window_state:
            self._settings.ui_preferences.window_state = window_state
        
        # Panel visibility
        self._settings.ui_preferences.control_panel_visible = self.qt_settings.value(
            "panels/control_visible", self._settings.ui_preferences.control_panel_visible, type=bool
        )
        self._settings.ui_preferences.log_panel_visible = self.qt_settings.value(
            "panels/log_visible", self._settings.ui_preferences.log_panel_visible, type=bool
        )
        
        # Application behavior
        self._settings.auto_connect_on_startup = self.qt_settings.value(
            "app/auto_connect_startup", self._settings.auto_connect_on_startup, type=bool
        )
        self._settings.enable_connection_monitoring = self.qt_settings.value(
            "app/enable_monitoring", self._settings.enable_connection_monitoring, type=bool
        )
    
    def _load_from_json_file(self):
        """Load settings from JSON file backup"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse connection config
            if 'tally_connection' in data:
                conn_data = data['tally_connection']
                # Map JSON keys to TallyConnectionConfig fields
                config_dict = {
                    'host': conn_data.get('default_host', 'localhost'),
                    'port': conn_data.get('default_port', 9000),
                    'timeout': conn_data.get('timeout_seconds', 30),
                    'retry_count': conn_data.get('retry_attempts', 3)
                }
                self._settings.connection = TallyConnectionConfig(**config_dict)
                logger.info(f"Loaded connection config from JSON: {self._settings.connection.url}")
            elif 'connection' in data:
                # Fallback for direct connection config format
                conn_data = data['connection']
                self._settings.connection = TallyConnectionConfig.from_dict(conn_data)
            
            # Parse UI preferences  
            if 'ui_preferences' in data:
                ui_data = data['ui_preferences']
                self._settings.ui_preferences = UIPreferences(**ui_data)
            
            # Parse connection history
            if 'connection_history' in data:
                self._settings.connection_history = data['connection_history']
            
            logger.debug("Settings loaded from JSON file")
            
        except Exception as e:
            logger.warning(f"Could not load JSON settings: {e}")
    
    def _apply_default_settings(self):
        """Apply default settings when loading fails"""
        self._settings = ApplicationSettings()
        logger.info(f"Default settings applied - connection will be: {self._settings.connection.url}")
    
    def save_settings(self):
        """
        Save current settings to both QSettings and JSON file
        Dual storage provides robustness and backup
        """
        try:
            # Save to Qt6 QSettings
            self._save_to_qt_settings()
            
            # Save to JSON file as backup
            self._save_to_json_file()
            
            logger.debug("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def _save_to_qt_settings(self):
        """Save settings to Qt6 QSettings storage"""
        
        # Connection settings
        self.qt_settings.setValue("connection/host", self._settings.connection.host)
        self.qt_settings.setValue("connection/port", self._settings.connection.port)
        self.qt_settings.setValue("connection/timeout", self._settings.connection.timeout)
        self.qt_settings.setValue("connection/retry_count", self._settings.connection.retry_count)
        
        # UI preferences
        self.qt_settings.setValue("ui/theme_name", self._settings.ui_preferences.theme_name)
        self.qt_settings.setValue("ui/font_family", self._settings.ui_preferences.font_family) 
        self.qt_settings.setValue("ui/font_size", self._settings.ui_preferences.font_size)
        
        # Panel visibility
        self.qt_settings.setValue("panels/control_visible", self._settings.ui_preferences.control_panel_visible)
        self.qt_settings.setValue("panels/log_visible", self._settings.ui_preferences.log_panel_visible)
        
        # Application behavior
        self.qt_settings.setValue("app/auto_connect_startup", self._settings.auto_connect_on_startup)
        self.qt_settings.setValue("app/enable_monitoring", self._settings.enable_connection_monitoring)
        
        # Ensure settings are written to storage
        self.qt_settings.sync()
    
    def _save_to_json_file(self):
        """Save settings to JSON file for backup and portability"""
        settings_data = {
            'connection': self._settings.connection.to_dict(),
            'ui_preferences': asdict(self._settings.ui_preferences),
            'connection_history': self._settings.connection_history,
            'auto_connect_on_startup': self._settings.auto_connect_on_startup,
            'check_for_updates': self._settings.check_for_updates,
            'enable_connection_monitoring': self._settings.enable_connection_monitoring,
            'monitoring_interval_seconds': self._settings.monitoring_interval_seconds,
            'default_export_format': self._settings.default_export_format,
            'max_records_per_query': self._settings.max_records_per_query
        }
        
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
    
    def update_connection_config(self, config: TallyConnectionConfig):
        """
        Update TallyPrime connection configuration
        
        Args:
            config: New connection configuration
        """
        old_config = self._settings.connection
        self._settings.connection = config
        
        # Add to connection history if it's a new configuration
        config_dict = config.to_dict()
        if config_dict not in self._settings.connection_history:
            self._settings.connection_history.insert(0, config_dict)
            # Keep only last 10 connections
            self._settings.connection_history = self._settings.connection_history[:10]
        
        # Save settings and emit signals
        self.save_settings()
        self.settings_changed.emit("connection_config", config)
        self.connection_config_changed.emit(config)
        
        logger.info(f"Connection config updated: {config.host}:{config.port}")
    
    def update_ui_preferences(self, preferences: UIPreferences):
        """
        Update UI preferences
        
        Args:
            preferences: New UI preferences
        """
        self._settings.ui_preferences = preferences
        
        # Save settings and emit signals
        self.save_settings()
        self.settings_changed.emit("ui_preferences", preferences)
        self.ui_preferences_changed.emit(preferences)
        
        logger.info("UI preferences updated")
    
    def save_window_geometry(self, geometry: Dict[str, int]):
        """
        Save window geometry for restoration on next startup
        
        Args:
            geometry: Dictionary with x, y, width, height keys
        """
        self._settings.ui_preferences.window_geometry = geometry
        self.qt_settings.setValue("window/geometry_dict", geometry)
        self.save_settings()
        
        logger.debug(f"Window geometry saved: {geometry}")
    
    def save_window_state(self, state: bytes):
        """
        Save window state (dock panels, toolbars, etc.)
        
        Args:
            state: Window state as bytes from QMainWindow.saveState()
        """
        self._settings.ui_preferences.window_state = state
        self.qt_settings.setValue("window/state", state)
        self.save_settings()
        
        logger.debug("Window state saved")
    
    def get_connection_history(self) -> List[TallyConnectionConfig]:
        """
        Get list of previously used connection configurations
        
        Returns:
            List of TallyConnectionConfig objects from history
        """
        configs = []
        for config_dict in self._settings.connection_history:
            try:
                config = TallyConnectionConfig.from_dict(config_dict)
                configs.append(config)
            except Exception as e:
                logger.warning(f"Invalid config in history: {e}")
        
        return configs
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of current settings
        
        Args:
            backup_name: Optional backup name, uses timestamp if None
            
        Returns:
            Path to the created backup file
        """
        if backup_name is None:
            from datetime import datetime
            backup_name = datetime.now().strftime("settings_backup_%Y%m%d_%H%M%S.json")
        
        if not backup_name.endswith('.json'):
            backup_name += '.json'
        
        backup_path = self.backup_dir / backup_name
        
        # Copy current settings to backup
        settings_data = {
            'connection': self._settings.connection.to_dict(),
            'ui_preferences': asdict(self._settings.ui_preferences),
            'connection_history': self._settings.connection_history,
            'auto_connect_on_startup': self._settings.auto_connect_on_startup,
            'check_for_updates': self._settings.check_for_updates,
            'enable_connection_monitoring': self._settings.enable_connection_monitoring,
            'monitoring_interval_seconds': self._settings.monitoring_interval_seconds,
            'created_timestamp': str(int(time.time())),
            'application_version': '1.0.0'
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Settings backup created: {backup_path}")
        return backup_path
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore settings from a backup file
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            bool: True if restore was successful, False otherwise
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate backup data structure
            required_keys = ['connection', 'ui_preferences']
            if not all(key in data for key in required_keys):
                logger.error("Invalid backup file structure")
                return False
            
            # Restore settings from backup
            old_settings = self._settings
            
            # Parse and apply backup data
            if 'connection' in data:
                self._settings.connection = TallyConnectionConfig.from_dict(data['connection'])
            
            if 'ui_preferences' in data:
                self._settings.ui_preferences = UIPreferences(**data['ui_preferences'])
            
            if 'connection_history' in data:
                self._settings.connection_history = data['connection_history']
            
            # Restore other settings
            for key in ['auto_connect_on_startup', 'check_for_updates', 
                       'enable_connection_monitoring', 'monitoring_interval_seconds']:
                if key in data:
                    setattr(self._settings, key, data[key])
            
            # Save restored settings
            self.save_settings()
            
            # Emit signals for UI updates
            self.connection_config_changed.emit(self._settings.connection)
            self.ui_preferences_changed.emit(self._settings.ui_preferences)
            
            logger.info(f"Settings restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def reset_to_defaults(self):
        """
        Reset all settings to default values
        Creates a backup before resetting
        """
        # Create backup before reset
        self.create_backup("before_reset")
        
        # Apply default settings
        old_settings = self._settings
        self._settings = ApplicationSettings()
        
        # Save default settings
        self.save_settings()
        
        # Emit signals for UI updates
        self.connection_config_changed.emit(self._settings.connection)
        self.ui_preferences_changed.emit(self._settings.ui_preferences)
        
        logger.info("Settings reset to defaults")


# Global settings manager instance
# This will be initialized by the main application
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """
    Get the global settings manager instance
    
    Returns:
        SettingsManager: The global settings manager
        
    Raises:
        RuntimeError: If settings manager is not initialized
    """
    global _settings_manager
    if _settings_manager is None:
        raise RuntimeError("SettingsManager not initialized. Call initialize_settings_manager() first.")
    return _settings_manager


def initialize_settings_manager(organization: str = "SrinidhiBS", 
                               application: str = "TallyPrimeManager") -> SettingsManager:
    """
    Initialize the global settings manager
    
    Args:
        organization: Organization name for settings storage
        application: Application name for settings storage
        
    Returns:
        SettingsManager: The initialized settings manager
    """
    global _settings_manager
    _settings_manager = SettingsManager(organization, application)
    return _settings_manager