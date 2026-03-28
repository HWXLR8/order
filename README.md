# Thermal Receipt Printer

A desktop application for sending print jobs to a network-connected thermal receipt printer.

## Features

- Print receipts to network thermal printers
- In-memory order history (last 100 orders)
- View and restore previous orders
- Configurable printer IP address

## Requirements

- Python 3.x
- Network-connected thermal printer (supports ESC/POS protocol)

## Installation

1. Clone or copy the files to your desired location
2. Install dependencies:
   ```bash
   pip install python-escpos
   ```
3. Configure the printer IP in `config.ini`:
   ```ini
   [printer]
   ip = 192.168.0.100
   ```

## Usage

### Running the Application

```bash
python3 order.py
```

### Command Line Options

- `--no-printer` - Run in test mode (prints to console instead of connecting to a printer)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Alt-s | Send to printer |
| Alt-i | Update printer IP |
| Alt-c | Clear form |
| Alt-h | View order history |

## Configuration

The printer IP address is stored in `config.ini` in the same directory as the executable. You can update it via the UI (Alt-i) or by editing the file directly.

## Order History

After each successful print, the order is saved to memory. Click the "History" button to view the last 100 orders. Select an order to restore its fields to the form for editing or re-printing.

## Building Standalone Executable

```bash
pyinstaller --onefile --noconsole --add-data "logo.png:." --collect-data escpos order.py
```

The executable will be created in the `dist/` directory.

**Note:** On Windows, use `--noconsole` to hide the terminal window. The `logo.png` and `escpos` data files must be bundled for the app to work correctly.
