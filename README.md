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
| **Backup** | Auto-backup on every app start (keeps last 5) |
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

### 7. Settings

```
Sidebar → Settings
```
- Switch between **Dark** and **Light** theme
- Manage backups (auto-backup + manual backup/restore)
- Export your data

---

## Where Is My Data Stored?

Your database file is saved at:
```
C:\Users\<YourName>\AppData\Roaming\InventoryManager\inventory.db
```

Backups are saved in the same folder under `backups/`.

> Tip: Copy the `inventory.db` file to a USB drive or cloud folder for extra safety.

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

## Build a Standalone .exe (Optional)

If you want to run the app without Python installed:

```
pip install pyinstaller
pyinstaller --onefile --windowed --name "InventoryManager" main.py
```

The `.exe` file will be in the `dist/` folder. You can copy it anywhere and run it directly.

---

## Project Structure

```
inventory-management/
├── main.py                 # App entry point
├── requirements.txt        # Python dependencies
├── database/
│   ├── connection.py       # SQLite database connection
│   └── schema.py           # Table creation
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
│   └── export_service.py   # Data export
└── ui/
    ├── styles.py           # Themes & styling
    ├── main_window.py      # Main window with sidebar
    ├── dashboard.py        # Dashboard overview
    ├── products_page.py    # Product management
    ├── purchase_page.py    # Record purchases
    ├── sales_page.py       # Record sales
    ├── inventory_page.py   # Stock levels
    ├── reports_page.py     # Reports & analytics
    └── settings_page.py    # App settings
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

---

## Tech Stack

- **Python 3.11** — Programming language
- **PySide6 (Qt6)** — Desktop UI framework
- **SQLite3** — Local database (built into Python)
