#!/usr/bin/env python3
"""
Logger Utility for TallyPrime Integration Manager

Simple logging utility for consistent logging across the application.
"""

import logging
import sys
from typing import Optional


def setup_logger(level: str = "INFO") -> None:
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name or __name__)