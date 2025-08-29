#!/usr/bin/env python3
"""
Theme Manager for TallyPrime Integration Manager
Centralized theme management with automatic dark/light theme detection

This module provides:
- Automatic Windows theme detection
- Consistent styling across all components
- Professional color schemes for both light and dark themes
- Easy theme switching capabilities

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
Date: August 27, 2025
"""

import logging
from typing import Dict, Any
from enum import Enum

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPalette
from PySide6.QtCore import QObject, Signal

# Set up logger
logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """Theme mode enumeration"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system theme


class ThemeColors:
    """
    Professional color schemes for light and dark themes
    
    Learning: Centralized color management for consistent theming
    """
    
    # Light theme colors (original professional palette)
    LIGHT = {
        'background': '#f8f9fa',
        'surface': '#ffffff',
        'surface_variant': '#ecf0f1',
        'primary': '#3498db',
        'primary_hover': '#2980b9',
        'primary_pressed': '#21618c',
        'secondary': '#2c3e50',
        'text_primary': '#2c3e50',
        'text_secondary': '#6c757d',
        'text_hint': '#6c757d',
        'border': '#bdc3c7',
        'border_light': '#dee2e6',
        'success': '#27ae60',
        'warning': '#f39c12',
        'error': '#e74c3c',
        'danger': '#e74c3c',
        'error_background': '#fdf2f2',
        'disabled': '#bdc3c7',
        'disabled_text': '#7f8c8d',
        'tab_background': '#ecf0f1',
        'tab_hover': '#d5dbdb',
        'selection': '#3498db',
        'selection_text': '#ffffff'
    }
    
    # Dark theme colors (modern dark palette)
    DARK = {
        'background': '#2d3748',
        'surface': '#1a202c',
        'surface_variant': '#2d3748',
        'primary': '#4299e1',
        'primary_hover': '#3182ce',
        'primary_pressed': '#2c5282',
        'secondary': '#e2e8f0',
        'text_primary': '#f7fafc',
        'text_secondary': '#e2e8f0',
        'text_hint': '#a0aec0',
        'border': '#4a5568',
        'border_light': '#4a5568',
        'success': '#48bb78',
        'warning': '#ed8936',
        'error': '#f56565',
        'danger': '#f56565',
        'error_background': '#742a2a',
        'disabled': '#4a5568',
        'disabled_text': '#a0aec0',
        'tab_background': '#2d3748',
        'tab_hover': '#4a5568',
        'selection': '#4299e1',
        'selection_text': '#ffffff'
    }


class ThemeManager(QObject):
    """
    Centralized theme manager for the application
    
    This class handles:
    - Automatic system theme detection
    - Consistent color scheme management
    - Theme change notifications
    - Professional styling generation
    
    Signals:
        theme_changed: Emitted when theme changes (theme_mode: ThemeMode)
    """
    
    # Signal emitted when theme changes
    theme_changed = Signal(ThemeMode)
    
    def __init__(self, parent=None):
        """
        Initialize the theme manager
        
        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        
        self._current_mode = ThemeMode.AUTO
        self._detected_mode = self.detect_system_theme()
        
        logger.info(f"Theme manager initialized - detected: {self._detected_mode.value}")
    
    @staticmethod
    def detect_system_theme() -> ThemeMode:
        """
        Detect current system theme mode
        
        Returns:
            ThemeMode: Detected theme mode (LIGHT or DARK)
            
        Learning: Use Qt's palette system to detect Windows theme
        """
        try:
            app = QApplication.instance()
            if app is None:
                return ThemeMode.LIGHT
            
            # Create a temporary widget to get system palette
            temp_widget = QWidget()
            palette = temp_widget.palette()
            
            # Check window background lightness
            window_color = palette.color(QPalette.Window)
            is_dark = window_color.lightness() < 128
            
            detected_mode = ThemeMode.DARK if is_dark else ThemeMode.LIGHT
            logger.info(f"System theme detected: {detected_mode.value} (lightness: {window_color.lightness()})")
            
            return detected_mode
            
        except Exception as e:
            logger.warning(f"Failed to detect system theme: {e}, defaulting to light")
            return ThemeMode.LIGHT
    
    @property
    def current_theme_mode(self) -> ThemeMode:
        """Get the current effective theme mode"""
        if self._current_mode == ThemeMode.AUTO:
            return self._detected_mode
        return self._current_mode
    
    @property
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark"""
        return self.current_theme_mode == ThemeMode.DARK
    
    @property
    def colors(self) -> Dict[str, str]:
        """Get current theme color palette"""
        if self.is_dark_theme:
            return ThemeColors.DARK
        return ThemeColors.LIGHT
    
    def set_theme_mode(self, mode: ThemeMode):
        """
        Set theme mode
        
        Args:
            mode: Theme mode to set
        """
        if mode != self._current_mode:
            old_effective_mode = self.current_theme_mode
            self._current_mode = mode
            
            # Update detected mode if set to auto
            if mode == ThemeMode.AUTO:
                self._detected_mode = self.detect_system_theme()
            
            # Emit signal if effective theme changed
            if self.current_theme_mode != old_effective_mode:
                self.theme_changed.emit(self.current_theme_mode)
                logger.info(f"Theme changed to: {self.current_theme_mode.value}")
    
    def refresh_system_theme(self):
        """
        Refresh system theme detection
        
        Useful when system theme changes while application is running
        """
        old_mode = self._detected_mode
        self._detected_mode = self.detect_system_theme()
        
        # If in auto mode and system theme changed, emit signal
        if (self._current_mode == ThemeMode.AUTO and 
            self._detected_mode != old_mode):
            self.theme_changed.emit(self.current_theme_mode)
            logger.info(f"System theme changed to: {self._detected_mode.value}")
    
    def get_stylesheet_for_widget(self, widget_type: str) -> str:
        """
        Get stylesheet for specific widget type
        
        Args:
            widget_type: Type of widget ('dialog', 'main_window', 'connection_widget', etc.)
            
        Returns:
            str: CSS stylesheet for the widget
        """
        colors = self.colors
        
        if widget_type == 'dialog':
            return self._get_dialog_stylesheet(colors)
        elif widget_type == 'connection_widget':
            return self._get_connection_widget_stylesheet(colors)
        elif widget_type == 'main_window':
            return self._get_main_window_stylesheet(colors)
        else:
            return self._get_base_stylesheet(colors)
    
    def _get_dialog_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate stylesheet for dialogs"""
        return f"""
            QDialog {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                font-family: "Segoe UI", Arial, sans-serif;
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin: 8px 0px;
                padding-top: 12px;
                background-color: {colors['surface']};
                color: {colors['text_primary']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: {colors['text_secondary']};
                background-color: {colors['surface']};
            }}
            
            QLabel {{
                color: {colors['text_secondary']};
                background-color: transparent;
            }}
            
            QLineEdit, QSpinBox {{
                border: 2px solid {colors['border_light']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                background-color: {colors['surface']};
                color: {colors['text_primary']};
            }}
            
            QLineEdit:focus, QSpinBox:focus {{
                border-color: {colors['primary']};
                outline: none;
            }}
            
            QLineEdit[invalid="true"] {{
                border-color: {colors['error']};
                background-color: {colors['error_background']};
            }}
            
            QPushButton {{
                background-color: {colors['primary']};
                border: none;
                color: white;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-height: 20px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['primary_pressed']};
            }}
            
            QPushButton:disabled {{
                background-color: {colors['disabled']};
                color: {colors['disabled_text']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                background-color: {colors['surface']};
                border-radius: 8px;
            }}
            
            QTabBar::tab {{
                background-color: {colors['tab_background']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                padding: 8px 16px;
                margin: 2px;
                border-radius: 6px;
                font-weight: bold;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {colors['tab_hover']};
            }}
            
            QListWidget {{
                border: 1px solid {colors['border']};
                border-radius: 6px;
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                alternate-background-color: {colors['surface_variant']};
            }}
            
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {colors['border_light']};
                color: {colors['text_primary']};
            }}
            
            QListWidget::item:selected {{
                background-color: {colors['selection']};
                color: {colors['selection_text']};
            }}
            
            QTextEdit {{
                border: 1px solid {colors['border']};
                border-radius: 6px;
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
            }}
            
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                color: {colors['text_primary']};
                background-color: {colors['surface_variant']};
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 3px;
            }}
            
            QCheckBox {{
                font-size: 12px;
                spacing: 8px;
                color: {colors['text_primary']};
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['surface']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors['primary']};
                border-color: {colors['primary']};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTggM0w0LjUgNi41TDIgNCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }}
            
            QSlider::groove:horizontal {{
                border: 1px solid {colors['border']};
                height: 8px;
                background: {colors['surface_variant']};
                border-radius: 4px;
            }}
            
            QSlider::handle:horizontal {{
                background: {colors['primary']};
                border: 1px solid {colors['primary']};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            
            QFrame[frameShape="4"] {{
                color: {colors['border']};
            }}
        """
    
    def _get_connection_widget_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate stylesheet for connection widget"""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin: 4px 0px;
                padding-top: 12px;
                background-color: {colors['surface']};
                color: {colors['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 6px 0 6px;
                color: {colors['text_secondary']};
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {colors['primary']};
                border: none;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                text-align: left;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary_pressed']};
            }}
            QPushButton:disabled {{
                background-color: {colors['disabled']};
                color: {colors['disabled_text']};
            }}
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                color: {colors['text_primary']};
                background-color: {colors['surface_variant']};
            }}
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 3px;
            }}
        """
    
    def _get_main_window_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate stylesheet for main window"""
        return f"""
            QMainWindow {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            QMenuBar {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border-bottom: 1px solid {colors['border']};
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QMenu {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
            }}
            QMenu::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QStatusBar {{
                background-color: {colors['secondary']};
                color: white;
                font-size: 11px;
            }}
            QDockWidget {{
                color: {colors['text_primary']};
                font-weight: bold;
            }}
            QDockWidget::title {{
                background-color: {colors['surface_variant']};
                color: {colors['text_primary']};
                padding: 4px;
                border-bottom: 1px solid {colors['border']};
            }}
        """
    
    def _get_base_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate base stylesheet for generic widgets"""
        return f"""
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                font-family: "Segoe UI", Arial, sans-serif;
            }}
        """


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """
    Get the global theme manager instance
    
    Returns:
        ThemeManager: Global theme manager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def is_dark_theme() -> bool:
    """
    Quick check if current theme is dark
    
    Returns:
        bool: True if dark theme is active
    """
    return get_theme_manager().is_dark_theme


def get_current_colors() -> Dict[str, str]:
    """
    Get current theme color palette
    
    Returns:
        Dict[str, str]: Current color scheme
    """
    return get_theme_manager().colors