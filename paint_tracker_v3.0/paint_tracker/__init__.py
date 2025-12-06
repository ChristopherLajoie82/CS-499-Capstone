"""
Paint Tracking System
Version 3.0.0

Three-layer architecture app for tracking paint jobs.
Refactored for CS 499 capstone project using PySide6/Qt6.
"""

__version__ = "3.0.0"
__author__ = "Christopher Lajoie"

from paint_tracker.data import JobRepository
from paint_tracker.core import (
    JobService, 
    ExportService, 
    BackupService, 
    AuthenticationService
)
from paint_tracker.ui import PaintTrackerApplication

__all__ = [
    'JobRepository',
    'JobService',
    'ExportService',
    'BackupService',
    'AuthenticationService',
    'PaintTrackerApplication',
    '__version__',
    '__author__'
]
