# uShare

A simple, elegant file sharing tool for local networks. Easily share files between devices with a web interface and QR code support.

## Screenshots

### Web Interface
![uShare Web Interface](placeholder-for-web-interface-screenshot.png)

### Terminal Usage
![uShare Terminal Usage](placeholder-for-terminal-usage-screenshot.png)

## Features

- **Simple File Sharing**: Share files quickly on your local network
- **Web Interface**: Works on all devices
- **QR Code Generation**: Easily connect from mobile devices by scanning a QR code
- **Multiple File Upload**: Upload multiple files at once
- **Cross-platform**: Works on any system with Python
- **Zero Configuration**: Just run and share

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/uniqueinx/ushare.git
   cd ushare
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make the script executable (optional):
   ```
   chmod +x ushare.py
   ```

## Usage

```
Usage: ushare.py [OPTIONS] COMMAND [ARGS]...

  A simple tool to share files via browser in a local network

Options:
  --help  Show this message and exit.

Commands:
  receive  Receive files from others on the network.
  send     Share a file with others on the network.
```
Examples:
```
ushare.py send file.txt
```
```
usharer.py receive -d ./Downloads
```
