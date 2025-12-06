# Paint Tracking System

A desktop application I built to solve a real problem at work - tracking paint mixes for production jobs in the sign and graphics shop. 

## What It Does

This application tracks paint usage for production jobs - job numbers, paint codes, manufacturers, colors, amounts, and who mixed what. 

**Core Features:**
- Track multiple colors per job 
- Paint version management 
- Job history - see every mix that's been done for a particular job number
- Search and filter (including last 30 days for recent work)
- Export to CSV or JSON for reporting
- Backup and restore 
- Customizable dropdowns - add manufacturers and operators on the fly with + buttons

**What Makes It Better Than the Original:**
- Not a monolithic mess anymore - properly separated into data, business logic, and UI layers
- PySide6/Qt6 interface instead of basic Tkinter
- Security considerations (parameterized SQL queries, input validation)
- Repository pattern for database access
- Service layer for business logic
- Professional error handling and logging

## How It's Built

This is a three-layer architecture application.

**Data Layer** (`paint_tracker/data/`)
- All database operations live here
- Repository pattern abstracts SQLite access
- Parameterized queries to prevent SQL injection
- Schema management with automatic column additions for upgrades

**Business Logic Layer** (`paint_tracker/core/`)
- ValidationService - checks that data makes sense before it hits the database
- JobService - coordinates between UI and database
- ExportService - handles CSV and JSON exports
- BackupService - manages database backups (keeps last 10)
- AuthenticationService - framework for security (stub implementation for now)

**Presentation Layer** (`paint_tracker/ui/`)
- PySide6/Qt6 framework (professional desktop UI)
- Main window with dashboard and job list
- Dialogs for job entry and history viewing
- Custom widgets for enhanced functionality

## Getting It Running

**What You Need:**
- Python 3.8 or newer
- pip (Python package manager)

**Setup:**

1. Grab the code:
```bash
git clone https://github.com/yourusername/paint-tracker.git
cd paint-tracker
```

2. Set up a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the requirements:
```bash
pip install -r requirements.txt
```

4. Run it:
```bash
python main.py
```

First time you run it, you'll be asked to select the location for the database file.

## Project Structure

Here's how the code is organized:

```
paint_tracker/
├── main.py                    # Start here - this is the entry point
├── requirements.txt           # Python dependencies (just PySide6 for now)
├── README.md                  
├── paint_tracker/             # Main package
│   ├── core/                 # Business logic layer
│   │   └── services.py       # All the service classes
│   ├── data/                 # Data access layer
│   │   └── repository.py     # JobRepository - all database operations
│   ├── ui/                   # Presentation layer
│   │   ├── main_window.py    # Main application window
│   │   ├── dialogs/          # Job form and detail dialogs
│   │   └── widgets/          # Custom dashboard widget
│   └── config/               # Configuration
│       └── settings.py       # Manages dropdown options
└── tests/                    # Unit tests (Empty for now will be added in the future)
```

## How to Use It

**Adding a Job:**
1. Click "New Job" button
2. Fill in the required information (job number, manufacturer, paint code, amount, etc.)
3. Select or add manufacturer and operator from the dropdowns (use the + button to add new ones)
4. Specify paint version (defaults to 1.0)
5. Add color name and notes if you want
6. Click Save

**Viewing Job History:**
- Click on any job in the main list
- You'll see every mix that's been done for that job, with dates and amounts
- Total paint used and all colors are shown at the top

**Searching:**
- Type in the search box (searches job number, color, paint code, operator)
- Toggle between "All Jobs" and "Last 30 Days"
- Click Search or just hit Enter

**Exporting Data:**
- File menu → Export to CSV (opens in Excel)
- File menu → Export to JSON (for data interchange or custom reports)

**Backups:**
- Tools menu → Create Backup (saves a timestamped copy)
- Tools menu → Restore from Backup (pick from the last 10 backups)
- Backups are stored in `~/.paint_tracker/backups/`

## For Developers

**Running Tests:**
```bash
python -m pytest tests/
```

**Code Style:**
I'm following PEP 8 guidelines.

**Making Changes:**
Because of the three-layer architecture, you can make changes in one layer without touching the others:
- Want to change the database? Only touch `data/repository.py`
- Want to add business logic? Only touch `core/services.py`
- Want to change the UI? Only touch `ui/` files


## The Backstory

This started as a 400-line monolithic file where everything was jammed together - UI code calling database code directly, no separation of concerns, minimal error handling. It worked, but it was definitely beginner code.

For my CS 499 capstone, I took that prototype and turned it into something I'd actually be comfortable showing to other developers. The enhanced version has:
- Three-layer architecture with proper separation
- Repository pattern for database access
- Service-oriented business logic
- Modern PySide6/Qt6 UI (way better than Tkinter)
- Security considerations throughout
- Professional error handling
- Backup and restore functionality
- Export capabilities

It's night and day difference between the original and the enhanced version. The original was functional but coupled and brittle. The enhanced version is professionally architected, secure, and maintainable.

## Technical Details

**Database:**
- SQLite 3 (lightweight, no server needed)
- Schema automatically migrates with new columns as needed
- Each row represents one paint mix event
- Job numbers can have multiple entries (sometimes you mix paint multiple times per job)

**Security:**
- All SQL queries use parameterized statements (no SQL injection)
- Input validation in both UI and business logic layers
- Error messages don't leak sensitive information
- Authentication framework in place (ready for bcrypt implementation)

**Data Storage:**
Everything lives in `~/.paint_tracker/`:
- `paint_tracker.db` - Main database
- `dropdown_settings.json` - Custom dropdown options
- `backups/` - Timestamped database backups (last 10 kept)
- `logs/` - Application logs

## Future Enhancements

The architecture is set up to support:
- bcrypt password hashing (framework is there, just needs the actual implementation)
- Multi-user support (would need to migrate from SQLite to PostgreSQL)
- Formula storage (actual paint recipes with ratios)
- Inventory integration
- Cloud backup(potentially)

For now, it does what it needs to do - track paint mixes for a small to medium shop.

## About This Project

**Author:** Christopher Lajoie  
**Context:** CS 499 Computer Science Capstone  
**School:** Southern New Hampshire University  
**Version:** 2.0.0

This is an educational project that demonstrates professional software engineering practices applied to a real-world problem.

The transformation from prototype to professional application showcases:
- Software architecture design (three-layer separation)
- Design patterns (Repository, Service Layer)
- Security mindset (defense in depth)
- Modern UI frameworks (PySide6/Qt6)
- Professional development practices

## License

This project is developed for educational purposes as part of the CS 499 capstone course at Southern New Hampshire University.