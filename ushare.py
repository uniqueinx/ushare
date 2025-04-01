#!/usr/bin/env python
import logging
import os
import socket
import sys
import re
import unicodedata

try:
    import typer
    import pyqrcode
    import uvicorn
    from fastapi import FastAPI, File, UploadFile
    from fastapi.responses import FileResponse, HTMLResponse
    from typing import List, Optional
except Exception:
    print(
        "Missing dependencies, Try pip install pyqrcode fastapi uvicorn python-multipart typer"
    )
    sys.exit(1)

uvicorn_logger = logging.getLogger("uvicorn")
fastapi_logger = logging.getLogger("fastapi")


def secure_filename(filename):
    """
    Return a secure version of a filename that is safe to store on the filesystem.
    """
    # Normalize unicode characters
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Remove illegal filesystem characters and sanitize the filename
    filename = re.sub(r"[^\w\s.-]", "", filename).strip()

    # Replace whitespace with underscores
    filename = re.sub(r"[\s]+", "_", filename)

    # If name was reduced to nothing, provide a default
    if not filename:
        filename = "unnamed_file"

    return filename


app = FastAPI()
app.config = {}
app.config["UPLOAD_FOLDER"] = os.getcwd()

gport = 9050
gfile = ""
gdirectory = os.getcwd()


def get_local_ip():
    """Get local IP address that other devices on the network can connect to."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable, just used to determine interface
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


ip_address = get_local_ip()


cli = typer.Typer(
    help="A simple tool to share files via browser in a local network",
    add_completion=False,
)


@app.get("/", response_class=HTMLResponse)
def index():
    return index_template


@app.get("/send")
def send_():
    try:
        file_path = os.path.join(gdirectory, gfile)
        if not os.path.exists(file_path):
            typer.echo("File not found, may be wrong path or filename.")
            sys.exit(1)
        return FileResponse(path=file_path, filename=gfile)
    except Exception:
        typer.echo("Error sending file.")
        sys.exit(1)


@app.get("/receive", response_class=HTMLResponse)
def receive_get():
    return upload_template


@app.post("/receive", response_class=HTMLResponse)
async def receive_post(files: List[UploadFile] = File(...)):
    if not files or len(files) == 0:
        return failed_send_template

    for file in files:
        if file.filename == "":
            return failed_send_template
        filename = secure_filename(file.filename)
        file_content = await file.read()
        with open(os.path.join(app.config["UPLOAD_FOLDER"], filename), "wb") as f:
            f.write(file_content)

    return success_template


def start_server(command: str, port: int, debug: bool = False):
    """Start the server with optional debug logging"""
    url = f"http://{ip_address}:{port}"
    qr = pyqrcode.create(url)
    typer.echo(qr.terminal(quiet_zone=1))
    typer.echo(f"Link: {url}")
    typer.echo(f"Mode: {command.capitalize()}")
    typer.echo(f"Local network IP: {ip_address}")

    if debug:
        uvicorn_logger.setLevel(logging.INFO)
        fastapi_logger.setLevel(logging.INFO)
        typer.echo("Debug mode: Enabled")
    else:
        uvicorn_logger.setLevel(logging.ERROR)
        fastapi_logger.setLevel(logging.ERROR)

    typer.echo("Ctrl+C to exit")
    log_level = "info" if debug else "error"
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=log_level)


@cli.command()
def send(
    file: str = typer.Argument(..., help="File to share", exists=True),
    port: int = typer.Option(gport, "--port", "-p", help="Port to use"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    Share a file with others on the network.

    Example:
        ushare send myfile.pdf
    """
    typer.echo(f"Sharing file: {file}")
    global gfile
    global gdirectory
    if file.count("/") > 1:
        gdirectory, gfile = file.rsplit("/", 1)
    else:
        gfile = file

    start_server("send", port, debug)


@cli.command()
def receive(
    directory: Optional[str] = typer.Option(
        None, "--directory", "-d", help="Folder where downloaded files will be saved"
    ),
    port: int = typer.Option(gport, "--port", "-p", help="Port to use"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    Receive files from others on the network.

    Example:
        ushare receive
        ushare receive --directory ~/Downloads
    """
    global upload_folder
    if directory:
        if not os.path.exists(directory):
            typer.echo(f"Directory {directory} does not exist")
            raise typer.Exit(1)
        typer.echo(f"Files will be saved to: {directory}")
        app.config["UPLOAD_FOLDER"] = directory

    start_server("receive", port, debug)


index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>uShare - File Sharing</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #2d3748;
            padding: 20px;
        }
        
        .container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .container:hover {
            transform: translateY(-5px);
        }
        
        h1 {
            margin-bottom: 20px;
            font-size: 28px;
            color: #4a5568;
        }
        
        .app-icon {
            font-size: 52px;
            margin-bottom: 20px;
            color: #4299e1;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }
        
        .button {
            flex: 1;
            background-color: #4299e1;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 15px 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .button:hover {
            background-color: #3182ce;
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        .button.download {
            background-color: #48bb78;
        }
        
        .button.download:hover {
            background-color: #38a169;
        }
        
        .description {
            color: #718096;
            margin: 20px 0;
            line-height: 1.6;
        }
        
        .footer {
            margin-top: 30px;
            font-size: 14px;
            color: #718096;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="app-icon">🔄</div>
        <h1>uShare</h1>
        <p class="description">
            A simple tool to share files between devices on your local network.
            Choose an option below to get started.
        </p>
        
        <div class="button-group">
            <a href="/receive" class="button">
                📤 Upload Files
            </a>
            <a href="/send" class="button download">
                📥 Download File
            </a>
        </div>
        
        <div class="footer">
            Secure, simple, and fast file sharing on your local network
        </div>
    </div>
</body>
</html>
"""

failed_send_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>uShare - Upload Failed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #2d3748;
            padding: 20px;
        }
        
        .container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .container:hover {
            transform: translateY(-5px);
        }
        
        h1 {
            margin-bottom: 20px;
            font-size: 28px;
            color: #e53e3e;
        }
        
        .error-icon {
            font-size: 52px;
            margin-bottom: 20px;
            color: #e53e3e;
        }
        
        .file-input-container {
            position: relative;
            margin-bottom: 25px;
            border: 2px dashed #a0aec0;
            border-radius: 8px;
            padding: 30px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .file-input-container:hover {
            border-color: #4299e1;
            background-color: #ebf8ff;
        }
        
        input[type="file"] {
            position: absolute;
            left: 0;
            top: 0;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .file-input-label {
            font-size: 16px;
            color: #718096;
        }
        
        .submit-btn {
            background-color: #4299e1;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 25px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            width: 100%;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .submit-btn:hover {
            background-color: #3182ce;
        }
        
        .back-btn {
            background-color: #718096;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 25px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            width: 100%;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
        }
        
        .back-btn:hover {
            background-color: #4a5568;
        }
        
        .footer {
            margin-top: 15px;
            font-size: 14px;
            color: #718096;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">⚠️</div>
        <h1>Upload Failed</h1>
        <form method="post" enctype="multipart/form-data">
            <div class="file-input-container">
                <input type="file" name="files" id="file-input" multiple>
                <div class="file-input-label">
                    <p>Drag files here or click to browse</p>
                    <p style="font-size: 13px; margin-top: 8px;">Supports multiple files</p>
                </div>
            </div>
            <button type="submit" class="submit-btn">Try Again</button>
        </form>
        <a href="/" class="back-btn">Back to Home</a>
        <div class="footer">
            Secure, simple, and fast file sharing
        </div>
    </div>
</body>
</html>
"""

success_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>uShare - Upload Successful</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #2d3748;
            padding: 20px;
        }
        
        .container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            padding: 30px;
            text-align: center;
        }
        
        .success-icon {
            font-size: 72px;
            margin-bottom: 20px;
            color: #48bb78;
        }
        
        h1 {
            color: #48bb78;
            margin-bottom: 15px;
            font-size: 28px;
        }
        
        p {
            color: #718096;
            margin-bottom: 25px;
            font-size: 16px;
        }
        
        .back-btn {
            background-color: #4299e1;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 25px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            display: inline-block;
            font-weight: 600;
            text-decoration: none;
            min-width: 180px;
        }
        
        .back-btn:hover {
            background-color: #3182ce;
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✅</div>
        <h1>Upload Successful!</h1>
        <p>Your files have been successfully shared.</p>
        <a href="/" class="back-btn">Back to Home</a>
    </div>
</body>
</html>
"""

upload_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>uShare - Upload Files</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #2d3748;
            padding: 20px;
        }
        
        .container {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            padding: 30px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .container:hover {
            transform: translateY(-5px);
        }
        
        h1 {
            margin-bottom: 20px;
            font-size: 28px;
            color: #4a5568;
        }
        
        .upload-icon {
            font-size: 52px;
            margin-bottom: 20px;
            color: #4299e1;
        }
        
        .file-input-container {
            position: relative;
            margin-bottom: 25px;
            border: 2px dashed #a0aec0;
            border-radius: 8px;
            padding: 30px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .file-input-container:hover {
            border-color: #4299e1;
            background-color: #ebf8ff;
        }
        
        input[type="file"] {
            position: absolute;
            left: 0;
            top: 0;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .file-input-label {
            font-size: 16px;
            color: #718096;
        }
        
        .submit-btn {
            background-color: #4299e1;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 25px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            width: 100%;
            font-weight: 600;
        }
        
        .submit-btn:hover {
            background-color: #3182ce;
        }
        
        .footer {
            margin-top: 15px;
            font-size: 14px;
            color: #718096;
        }
        
        .footer a {
            color: #4299e1;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="upload-icon">📤</div>
        <h1>uShare</h1>
        <form method="post" enctype="multipart/form-data">
            <div class="file-input-container">
                <input type="file" name="files" id="file-input" multiple>
                <div class="file-input-label">
                    <p>Drag files here or click to browse</p>
                    <p style="font-size: 13px; margin-top: 8px;">Supports multiple files</p>
                </div>
            </div>
            <button type="submit" class="submit-btn">Upload Files</button>
        </form>
        <div class="footer">
            <a href="/">Back to Home</a>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    cli()
