# Ushare
A very simple script that helps me share file between laptops and phones via terminals and browsers on a local network.

# Usage
```
ushare.py [OPTIONS] COMMAND [ARGS]...
Options:
  --help  Show this message and exit.
Commands:
  receive  Receive files
  send     Serve shared file
  ```
Examples:
```
ushare.py send file.txt
```
```
usharer.py receive -d ./Downloads
```
# Requirements 
flask, pyqrcode, you can install them via 
```
pip install flask pyqrcode
```
