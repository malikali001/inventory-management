# Inventory Manager

A simple offline desktop app to manage your **inventory**, **purchases**, **sales**, and **profits** — built for wholesale and retail businesses.

> No internet needed. No monthly fees. Your data stays on your computer.

---

## What Can It Do?

| Feature | Description |
|---------|-------------|
| **Products** | Add products with custom units (piece, dozen, box, etc.) |
| **Purchases** | Record what you buy from suppliers |
| **Sales** | Record what you sell to customers |
| **Inventory** | See current stock levels with low-stock alerts |
| **Reports** | View daily summaries, profit per product, and history |
| **Backup** | Auto-backup on app close (keeps last 5), manual backup/restore |
| **Google Drive** | Optional cloud sync for backups (requires credentials.json) |
| **User Guide** | Built-in guide with visual diagrams for every feature |
| **Themes** | Switch between dark and light mode |
| **Export** | Export reports and data |

---

## Setup (Step by Step)

### Step 1: Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download **Python 3.11** or newer
3. Run the installer
4. **Important:** Check the box that says **"Add Python to PATH"** before clicking Install

To verify, open **Command Prompt** and type:
```
python --version
```
You should see something like `Python 3.11.x`

---

### Step 2: Download This Project

**Option A — If you have Git:**
```
git clone <repository-url>
cd inventory-management
```

**Option B — Without Git:**
1. Download the ZIP file of this project
2. Extract it to a folder (e.g. `C:\Users\YourName\Documents\inventory-management`)
3. Open **Command Prompt** and navigate to that folder:
```
cd C:\Users\YourName\Documents\inventory-management
```

---

### Step 3: Install Dependencies

Run this command in the project folder:
```
pip install -r requirements.txt
```
This installs **PySide6** (the UI framework). It may take a minute.

---

### Step 4: Run the App

```
python main.py
```

The app window will open — you're ready to go!

---

## How to Use

### 1. Add Your Products

```
Sidebar → Products → + Add Product
```
- Enter the product name
- Set the **base unit** (e.g. "piece", "kg", "meter")
- Set a **low stock threshold** (you'll get alerts when stock drops below this)

### 2. Add Extra Units (Optional)

```
Products Page → Click "Units" icon on a product
```
- Example: If base unit is "piece", add "dozen" with conversion = 12
- This means 1 dozen = 12 pieces in your inventory

### 3. Record a Purchase (When You Buy Stock)

```
Sidebar → Record Purchase
```
- Select the supplier date
- Add products, choose unit, enter quantity and price
- Click **Save** — your inventory goes up

### 4. Record a Sale (When You Sell)

```
Sidebar → Enter Sales
```
- Add products you sold, enter quantity and price
- Click **Save** — your inventory goes down

### 5. Check Your Inventory

```
Sidebar → Inventory
```
- See all products with current stock
- Products below the low-stock threshold are highlighted

### 6. View Reports

```
Sidebar → Reports
```
- **Daily Summary** — total purchases, sales, and profit for any date
- **Profit by Product** — see which products make the most money
- **Purchase History** — all past purchases
- **Sales History** — all past sales

### 7. User Guide

```
Sidebar → User Guide
```
- Step-by-step instructions with visual flow diagrams
- Covers products, purchases, sales, inventory, reports, and backups

### 8. Settings

```
Sidebar → Settings
```
- Switch between **Dark** and **Light** theme
- Manage backups (auto-backup + manual backup/restore)
- Connect Google Drive for automatic cloud sync
- Export your data

---

## Where Is My Data Stored?

| Platform | Data Folder |
|----------|-------------|
| Windows | `%APPDATA%\InventoryManager\` |
| macOS | `~/Library/Application Support/InventoryManager/` |
| Linux | `~/.local/share/InventoryManager/` |

Inside that folder you'll find:
- `inventory.db` — your database
- `app.log` — application log
- `backups/` — auto-backup files

> Tip: Copy the `inventory.db` file to a USB drive or cloud folder for extra safety.
> Or connect Google Drive in Settings for automatic cloud backup.

---

## How the App Works (Overview)

```
┌─────────────────────────────────────────────────┐
│                 Inventory Manager                │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ Sidebar  │          Main Content Area           │
│          │                                      │
│ Dashboard│  ┌──────────────────────────────┐    │
│ Products │  │  Each page shows forms and   │    │
│ Purchase │  │  tables for managing data    │    │
│ Sales    │  │                              │    │
│ Inventory│  └──────────────────────────────┘    │
│ Reports  │                                      │
│ Guide    │                                      │
│ Settings │                                      │
│          │                                      │
├──────────┴──────────────────────────────────────┤
│              Status Bar / Version               │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
Purchase ──→ Inventory ←── Sale
   │            │            │
   │            ▼            │
   │     Stock goes UP       │
   │     Stock goes DOWN ────┘
   │
   └──→ Reports (profit = sale price - purchase price)
```

---

## Google Drive Backup (Optional)

To enable automatic cloud backup:

1. Get a `credentials.json` file (Google OAuth client credentials)
2. Place it in your data folder:
   ```
   C:\Users\<YourName>\AppData\Roaming\InventoryManager\credentials.json
   ```
3. Go to **Settings → Google Drive Backup → Connect Google Drive**
4. Sign in with your Google account in the browser
5. Backups will now sync to a `InventoryManager_Backups` folder on your Drive

> If you don't have a `credentials.json` file, the Settings page will show instructions. Contact your administrator for the file.

---

## Build Standalone App (Optional)

Build a self-contained executable — no Python installation needed on the target machine.

### Prerequisites

```
pip install pyinstaller
```

### Build for Current Platform

```
python build.py
```

Or with a clean build (removes previous artifacts):

```
python build.py --clean
```

### Platform Output

| Platform | Output | Data Location |
|----------|--------|---------------|
| Windows | `dist/InventoryManager.exe` | `%APPDATA%\InventoryManager\` |
| macOS | `dist/InventoryManager.app` | `~/Library/Application Support/InventoryManager/` |
| Linux | `dist/InventoryManager` | `~/.local/share/InventoryManager/` |

### Distribute

- **Windows:** Send `InventoryManager.exe` — users double-click to run
- **macOS:** Send `InventoryManager.app` — users drag to Applications folder
- **Linux:** Send `InventoryManager` binary — users run `chmod +x InventoryManager && ./InventoryManager`

---

## Project Structure

```
inventory-management/
├── main.py                 # App entry point
├── version.py              # App version (single source of truth)
├── build.py                # Cross-platform build script
├── InventoryManager.spec   # PyInstaller configuration
├── requirements.txt        # Python dependencies
├── assets/
│   ├── icon.png            # App icon (source, 512x512)
│   ├── icon.ico            # Windows icon
│   └── icon.icns           # macOS icon
├── database/
│   ├── connection.py       # SQLite database connection
│   ├── schema.py           # Table creation
│   └── migrations.py       # Schema migration runner
├── models/
│   ├── product.py          # Product & unit data models
│   ├── purchase.py         # Purchase data model
│   └── sale.py             # Sale data model
├── services/
│   ├── product_service.py  # Product CRUD operations
│   ├── purchase_service.py # Purchase logic
│   ├── sale_service.py     # Sale logic
│   ├── inventory_service.py# Stock calculations
│   ├── report_service.py   # Report generation
│   ├── backup_service.py   # Auto & manual backups
│   ├── export_service.py   # Data export
│   └── google_drive_service.py  # Google Drive cloud sync
└── ui/
    ├── styles.py           # Themes & styling
    ├── main_window.py      # Main window with sidebar
    ├── dashboard.py        # Dashboard overview
    ├── products_page.py    # Product management
    ├── purchase_page.py    # Record purchases
    ├── sales_page.py       # Record sales
    ├── inventory_page.py   # Stock levels
    ├── reports_page.py     # Reports & analytics
    ├── guide_page.py       # Built-in user guide
    └── settings_page.py    # App settings & backups
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` command not found | Make sure Python is added to PATH (reinstall and check the box) |
| `pip` command not found | Try `python -m pip install -r requirements.txt` instead |
| App won't start | Make sure you're in the project folder and ran `pip install -r requirements.txt` |
| Can't find my data | Check `%APPDATA%\InventoryManager\` in File Explorer |
| Want to reset everything | Delete `inventory.db` from the AppData folder and restart the app |
| Google Drive won't connect | Make sure `credentials.json` is in the AppData folder |
| App shows errors | Check `app.log` in the AppData folder for details |

---

## Tech Stack

- **Python 3.11** — Programming language
- **PySide6 (Qt6)** — Desktop UI framework
- **SQLite3** — Local database (built into Python)
