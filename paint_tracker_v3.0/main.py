#!/usr/bin/env python3
"""
Paint Tracking System - Main Entry Point

This is the main entry point for the Paint Tracking System application.
Run this file to start the application.

Author: Christopher Lajoie
Version: 3.0.0
Course: CS 499 - Computer Science Capstone

Requirements:
- Python 3.8+
- PySide6
- bcrypt
- psycopg2-binary (for PostgreSQL support)
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paint_tracker.ui import PaintTrackerApplication


def setup_logging():
    """Configure application logging"""
    log_dir = Path.home() / ".paint_tracker" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "paint_tracker.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('paint_tracker').setLevel(logging.DEBUG)
    
    return logging.getLogger(__name__)


def check_requirements():
    """Check if required packages are installed"""
    try:
        import PySide6
        return True
    except ImportError:
        return False


def main():
    """Main function to run the application"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Paint Tracking System v3.0.0")
    
    # Check requirements
    if not check_requirements():
        logger.error("PySide6 is not installed. Please install it using: pip install PySide6")
        print("\nERROR: PySide6 is required to run this application.")
        print("Please install it using: pip install PySide6")
        print("\nOr install all requirements using: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        # Create and run the application
        app = PaintTrackerApplication()
        result = app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)
    
    logger.info("Application closed")
    sys.exit(result)


if __name__ == "__main__":
    main()
