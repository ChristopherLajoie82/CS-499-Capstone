# Paint Tracking System

A desktop application I built to solve a real problem at work - tracking paint mixes for production jobs in the sign and graphics shop. 

## What It Does

This application tracks paint usage for production jobs - job numbers, paint codes, manufacturers, colors, amounts, and who mixed what. 

**Core Features:**
- Track multiple colors per job 
- Paint version management 
- **Paint mix calculator** - automatically calculates component amounts using industry-standard ratios (3:1:3 for interior, 3:1:1 for exterior)
- Job history - see every mix that's been done for a particular job number
- Search and filter by job number or operator
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

**Algorithm Layer** (`paint_tracker/algorithms/`)
- Paint mix calculator using industry-standard ratios
- Interior formula: 3:1:3 (paint : catalyst : additive)
- Exterior formula: 3:1:1 (paint : catalyst : reducer)
- Enter your paint amount, get exact component quantities
- O(1) time complexity - simple ratio math, no loops or recursion

**Data Layer** (`paint_tracker/data/`)
- All database operations live here
- Repository pattern abstracts SQLite access
- Parameterized queries to prevent SQL injection
- Schema management with automatic column additions for upgrades

**Business Logic Layer** (`paint_tracker/core/`)
- ValidationService - checks that data makes sense before it hits the database
- JobService - coordinates between UI and database
- PaintCalculatorService - wraps the algorithm layer for mix calculations
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

3. Install PySide6:
```bash
pip install PySide6
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
├── README.md                  
├── CHANGELOG.md              # Recent changes and updates
├── paint_tracker/             # Main package
│   ├── algorithms/           # Algorithm layer
│   │   └── paint_calculator.py  # Mix ratio calculations
│   ├── core/                 # Business logic layer
│   │   └── services.py       # All the service classes
│   ├── data/                 # Data access layer
│   │   └── repository.py     # JobRepository - all database operations
│   ├── ui/                   # Presentation layer
│   │   ├── main_window.py    # Main application window and dashboard
│   │   └── dialogs/          # Job form dialog
│   └── config/               # Configuration
│       └── settings.py       # Manages dropdown options
```

## How to Use It

**Adding a Job:**
1. Click "New Job" button
2. Fill in the required information (job number, manufacturer, paint code, amount, etc.)
3. Select job type (Interior or Exterior) - this determines the mixing ratio
4. Enter total paint amount and click "Calculate Mix" to see the component breakdown
5. Select or add manufacturer and operator from the dropdowns (use the + button to add new ones)
6. Specify paint version (defaults to 1.0)
7. Add color name and notes if you want
8. Click Save

**Using the Paint Calculator:**
- Select Interior (3:1:3 ratio) or Exterior (3:1:1 ratio)
- Enter the total paint amount you need
- Click "Calculate Mix" 
- The form shows you exactly how much paint, catalyst, and additive/reducer to measure
- These amounts are saved with the job for future reference

**Viewing Job History:**
- Click on any job in the main list
- You'll see every mix that's been done for that job, with dates and amounts

**Searching:**
- Type in the search box to filter by job number or operator
- Click Search or just hit Enter
- Click Clear to reset the search

**Exporting Data:**
- File menu → Export to CSV (opens in Excel)
- File menu → Export to JSON (for data interchange or custom reports)

**Backups:**
- Tools menu → Create Backup (saves a timestamped copy)
- Tools menu → Restore from Backup (pick from the last 10 backups)
- Backups are stored in `~/.paint_tracker/backups/`

## For Developers

**Code Style:**
I'm following PEP 8 guidelines.

**Making Changes:**
Because of the three-layer architecture, you can make changes in one layer without touching the others:
- Want to change the database? Only touch `data/repository.py`
- Want to add business logic? Only touch `core/services.py`
- Want to change the UI? Only touch `ui/` files


## The Backstory

This started as a 400-line file where everything was jammed together - UI code calling database code directly, no separation of concerns, minimal error handling. It worked, but it was definitely beginner code.

For my CS 499 capstone, I took that prototype and turned it into something I'd actually be comfortable showing to other developers. Enhancement One refactored the architecture, and Enhancement Two added the paint mix calculator algorithm. The enhanced version now has:
- Three-layer architecture with proper separation
- Repository pattern for database access
- Service-oriented business logic
**Technical Details:**
- **Paint mix calculator with industry-standard ratios**
- Coverage estimation algorithm (implemented but not exposed in UI - future feature)
- Modern PySide6/Qt6 UI (way better than Tkinter)
- Security considerations throughout
- Professional error handling
- Backup and restore functionality
- Export capabilities

## Technical Details

**Database:**
- SQLite 3 
- Schema automatically migrates with new columns as needed
- Each row represents one paint mix event
- Job numbers can have multiple entries (some jobs have multiple colors)

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

**PostgreSQL Migration**
- Migrate from SQLite to PostgreSQL for better multi-user support and scalability
- Would allow concurrent access from multiple workstations
- Better suited for network deployment in larger shops

**User Accounts**
- Login system with bcrypt password hashing
- Role-based access (operator vs admin)
- Track which user created each entry
- Auto-fill "Mixed By" field based on logged-in user
- Admin controls for user management and system settings

**PDF Attachment System**
- Attach paint code PDFs to job entries
- Store files in dedicated attachments folder with database references
- View attachments directly from job history
- Keep paint specifications linked to actual usage records

**PDF Parsing for Paint Codes**
- Extract paint code information automatically from manufacturer PDFs
- Parse color formulas, ratios, and specifications
- Auto-populate job form fields from uploaded paint sheets
- Reduce manual data entry and transcription errors

**Other Potential Features**
- Inventory integration and stock tracking
- Cloud backup options
- Reporting and analytics dashboard
- Mobile companion app for shop floor use

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