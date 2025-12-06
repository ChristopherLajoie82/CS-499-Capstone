# Paint Tracking System

**CS 499 Computer Science Capstone — Southern New Hampshire University**

A desktop application for tracking paint usage, calculating mix ratios, and managing production data in a sign and graphics manufacturing environment. This project demonstrates the transformation of a 400-line prototype into a 14,000+ line production-ready application through three systematic enhancements.

## About This Project

This isn't just a capstone artifact—it's a working application that solves real problems I encountered during my 21 years in the skilled trades. After 17 years as an automotive paint technician and 4 years in sign manufacturing, I built this tool to address actual workflow and data tracking challenges on the production floor.

The application allows users to:
- Track paint usage by job number
- Calculate component breakdowns using industry-standard mixing ratios
- Manage user authentication with role-based access control
- Export data for reporting and analysis
- View job history and production statistics

## Repository Structure

```
CS-499-Capstone/
├── paint_tracker/          # Original artifact (~400 lines)
├── paint_tracker_v1.0/     # Enhancement One: Software Design
├── paint_tracker_v2.0/     # Enhancement Two: Algorithms
├── paint_tracker_v3.0/     # Enhancement Three: Databases
└── README.md
```

## Enhancement Overview

### Original Artifact: `paint_tracker/`
The starting point—a functional but monolithic Python script using Tkinter and SQLite. Everything was in one file with no separation of concerns, minimal error handling, and no security considerations. It worked, but it was very much beginner's code.

### Enhancement One: Software Design and Engineering (`paint_tracker_v1.0/`)
Refactored the monolithic script into a professionally architected application:
- **Three-layer architecture**: Data Access Layer, Business Logic Layer, Presentation Layer
- **Repository pattern**: All database access encapsulated with parameterized queries
- **PySide6/Qt6**: Migrated from Tkinter to a modern, professional UI framework
- **Comprehensive error handling**: Try-except blocks with logging throughout

### Enhancement Two: Algorithms and Data Structures (`paint_tracker_v2.0/`)
Added the core computational engine that makes this tool actually useful:
- **PaintMixCalculator**: O(1) constant-time complexity for component calculations
- **Industry-standard ratios**: 3:1:3 for interior jobs, 3:1:1 for exterior jobs
- **Job summary aggregation**: Groups individual mixes by job number with calculated totals
- **Mix Detail Dialog**: UI for viewing calculation breakdowns

### Enhancement Three: Databases (`paint_tracker_v3.0/`)
Completed the transformation into a production-ready application:
- **bcrypt password hashing**: Work factor 12 (~250ms per hash)
- **Account lockout**: 5 failed attempts triggers 15-minute ban
- **Role-based access control**: Admin vs. user permissions
- **Foreign key relationships**: Audit trail linking jobs to users
- **Repository Factory pattern**: SQLite for single-user, PostgreSQL for multi-user deployments
- **Constant-time password comparison**: Prevents timing attacks

## Technology Stack

- **Language**: Python 3.x
- **UI Framework**: PySide6/Qt6
- **Databases**: SQLite (single-user), PostgreSQL (multi-user)
- **Security**: bcrypt for password hashing
- **Architecture**: Three-layer with Repository pattern

## Installation

### Requirements
```
Python 3.8+
PySide6
bcrypt
psycopg2 (for PostgreSQL support)
```

### Setup
```bash
# Clone the repository
git clone https://github.com/ChristopherLajoie82/CS-499-Capstone.git
cd CS-499-Capstone

# Install dependencies
pip install PySide6 bcrypt psycopg2-binary

# Run the latest version
cd paint_tracker_v3.0
python main.py
```

## ePortfolio

For the full narrative documentation, code review video, and professional self-assessment, visit my ePortfolio:

**[https://christopherlajoie82.github.io/](https://christopherlajoie82.github.io/)**

## Author

**Christopher Lajoie**
- Email: lajoiechristopher82@gmail.com
- GitHub: [ChristopherLajoie82](https://github.com/ChristopherLajoie82)
- LinkedIn: [christopher-lajoie-82063430b](https://www.linkedin.com/in/christopher-lajoie-82063430b/)

## License

This project was developed as part of the CS 499 Computer Science Capstone at Southern New Hampshire University.
