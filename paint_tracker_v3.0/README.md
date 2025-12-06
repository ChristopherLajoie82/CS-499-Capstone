# Paint Tracking System

A desktop application I built to solve a real problem at work - tracking paint mixes for production jobs in the sign and graphics shop. 

## What It Does

This application tracks paint usage for production jobs - job numbers, paint codes, manufacturers, colors, amounts, and who mixed what. 

**Core Features:**
- Track multiple colors per job 
- Paint version management 
- Job history - see every mix that's been done for a particular job number
- Search and filter by job number or operator
- Export to CSV or JSON for reporting
- Backup and restore 
- Customizable dropdowns - add manufacturers and operators on the fly with + buttons
- **Paint mix calculator** - automatically calculates component amounts using industry-standard ratios (3:1:3 for interior, 3:1:1 for exterior)
- **PDF attachments** - attach paint specification sheets to jobs and access them from the job history
- **Multi-user support with PostgreSQL** - multiple workstations can access the same database
- **User authentication** - login system with bcrypt password hashing and role-based access control

**What Makes It Better Than the Original:**
- Not a monolithic mess anymore - properly separated into data, business logic, and UI layers
- PySide6/Qt6 interface instead of basic Tkinter
- Security considerations (parameterized SQL queries, input validation, bcrypt hashing)
- Repository pattern for database access
- Service layer for business logic
- Professional error handling and logging
- **Database flexibility** - choose between SQLite (single-user) or PostgreSQL (multi-user)

## How It's Built

This is a three-layer architecture application.

**Data Layer** (`paint_tracker/data/`)
- All database operations live here
- Repository pattern abstracts database access
- **Supports both SQLite and PostgreSQL** - seamlessly switch between databases
- Repository Factory Pattern for database type abstraction
- Separate repositories for jobs, users, and attachments
- Parameterized queries to prevent SQL injection
- Schema management with automatic table creation
- Connection pooling for PostgreSQL concurrent access

**Business Logic Layer** (`paint_tracker/core/`)
- ValidationService - checks that data makes sense before it hits the database
- JobService - coordinates between UI and database
- ExportService - handles CSV and JSON exports
- BackupService - manages database backups (keeps last 10)
- AuthenticationService - bcrypt password hashing, session management, role-based access control
- AttachmentService - manages PDF file storage and retrieval
- PaintCalculatorService - paint mixing calculations with industry ratios

**Presentation Layer** (`paint_tracker/ui/`)
- PySide6/Qt6 framework (professional desktop UI)
- Main window with dashboard and job list
- Login dialog with authentication flow
- Dialogs for job entry, history viewing, user management, database settings
- Attachments dialog for managing PDF files
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

This installs:
- **PySide6**: Qt6 framework for the UI
- **bcrypt**: Secure password hashing
- **psycopg2-binary**: PostgreSQL database driver (optional, only needed for multi-user setup)

4. Run it:
```bash
python main.py
```

First time you run it, you'll be asked to:
1. Select the location for the database file (SQLite mode)
2. Create your administrator account (username and password)

After initial setup, you'll log in with your credentials each time you start the application.

**For Multi-User PostgreSQL Setup:**
See [POSTGRESQL_MIGRATION_GUIDE.md](POSTGRESQL_MIGRATION_GUIDE.md) for detailed instructions on:
- Setting up a PostgreSQL server
- Configuring network access
- Switching from SQLite to PostgreSQL
- Multi-workstation deployment

## Project Structure

Here's how the code is organized:

```
paint_tracker/
├── main.py                    # Start here - this is the entry point
├── requirements.txt           # Python dependencies
├── README.md                  
├── paint_tracker/             # Main package
│   ├── algorithms/           # Algorithm layer
│   │   └── paint_calculator.py  # Mix ratio calculations
│   ├── core/                 # Business logic layer
│   │   ├── services.py       # Job, Export, Backup, Validation services
│   │   ├── auth_service.py   # Authentication with bcrypt
│   │   └── attachment_service.py  # PDF attachment management
│   ├── data/                 # Data access layer
│   │   ├── repository.py     # JobRepository - SQLite job operations
│   │   ├── repository_postgres.py  # JobRepository - PostgreSQL version
│   │   ├── repository_factory.py   # Creates the right repository type
│   │   ├── user_repository.py      # UserRepository - SQLite user management
│   │   └── user_repository_postgres.py  # UserRepository - PostgreSQL version
│   ├── ui/                   # Presentation layer
│   │   ├── main_window.py    # Main application window and dashboard
│   │   ├── attachments_dialog.py  # PDF attachment management UI
│   │   ├── database_settings_dialog.py  # Database configuration UI
│   │   └── dialogs/          # Job form, login dialogs
│   └── config/               # Configuration
│       ├── settings.py       # Manages dropdown options
│       └── database_config.py  # Database connection settings
```

## How to Use It

**Adding a Job:**
1. Click "New Job" button
2. Fill in the required information (job number, manufacturer, paint code, amount, etc.)
3. Select job type (Interior or Exterior) for automatic ratio calculation
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

**Attaching PDFs:**
- Open a job's history by double-clicking it
- Click "Attachments" to open the attachment manager
- Add paint specification sheets, safety data sheets, or any relevant PDFs
- View or delete attachments as needed
- Attachments are stored locally and linked to the job in the database

**Viewing Job History:**
- Double-click any job in the main list
- You'll see every mix that's been done for that job, with dates and amounts
- Total paint used and all colors are shown at the top
- Access attachments from here too

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

**Code Style:**
I'm following PEP 8 guidelines.

**Making Changes:**
Because of the three-layer architecture, you can make changes in one layer without touching the others:
- Want to change the database? Only touch `data/repository.py`
- Want to add business logic? Only touch `core/services.py`
- Want to change the UI? Only touch `ui/` files

**Switching Databases:**
The Repository Factory pattern means you can switch between SQLite and PostgreSQL without changing any business logic or UI code. Just update the database configuration.

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
- Real user authentication with bcrypt
- PDF attachment system

It's night and day difference between the original and the enhanced version. The original was functional but coupled and brittle. The enhanced version is professionally architected, secure, and maintainable.

## Technical Details

**Database:**
- SQLite 3 or PostgreSQL (your choice)
- Three tables: jobs, users, attachments
- Schema automatically migrates with new columns as needed
- Users table with role-based access control
- Jobs table with foreign key to users
- Attachments table linked to jobs by job number
- Indexes on frequently queried columns (job_number, user_id, created_at)
- Each row represents one paint mix event
- Job numbers can have multiple entries (sometimes you mix paint multiple times per job)

**Security:**
- All SQL queries use parameterized statements (no SQL injection)
- Input validation in both UI and business logic layers
- Error messages don't leak sensitive information
- bcrypt password hashing with automatic salt generation (work factor 12)
- Account lockout after 5 failed login attempts (15 minute lockout)
- Role-based access control (admin vs user)
- Foreign key relationships for data integrity
- Constant-time password comparison to prevent timing attacks
- Password strength requirements enforced

**Authentication:**
- Login required at application startup
- Initial setup wizard creates first admin account
- Password strength requirements enforced (8+ chars, mixed case, numbers, special chars)
- Admins can create additional users and manage roles
- Users can change their own passwords
- Session tracking throughout application

**Data Storage:**
Everything lives in `~/.paint_tracker/`:
- `paint_tracker.db` - Main database (jobs, users, attachments)
- `dropdown_settings.json` - Custom dropdown options
- `attachments/` - PDF files linked to jobs
- `backups/` - Timestamped database backups (last 10 kept)
- `logs/` - Application logs

## Future Enhancements

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
**Version:** 3.0.0

This is an educational project that demonstrates professional software engineering practices applied to a real-world problem.

### Enhancement History

**Enhancement One - Software Design/Engineering**
- Three-layer architecture (Data, Business Logic, Presentation)
- Migration from Tkinter to PySide6/Qt6
- Repository and Service patterns
- Comprehensive input validation

**Enhancement Two - Algorithms and Data Structures**
- Paint mix calculator with industry-standard ratios (3:1:3, 3:1:1)
- O(1) time complexity for calculations
- Component breakdown for interior/exterior jobs
- Coverage estimation algorithm

**Enhancement Three - Databases**
- User authentication with bcrypt password hashing
- Users table with role-based access control
- Attachments table for PDF file management
- Foreign key linking jobs to users
- Database indexes for query performance
- Account lockout protection
- Session management
- Repository Factory pattern for SQLite/PostgreSQL flexibility
- PostgreSQL support for multi-user deployment

The transformation from prototype to professional application showcases:
- Software architecture design (three-layer separation)
- Design patterns (Repository, Factory, Service Layer)
- Security mindset (defense in depth)
- Modern UI frameworks (PySide6/Qt6)
- Professional development practices

## License

This project is developed for educational purposes as part of the CS 499 capstone course at Southern New Hampshire University.
