#!/usr/bin/env python
import logging
import os
import socket
import sys

import eventlet
from eventlet import wsgi

try:
    import click
    import pyqrcode
    from flask import Flask, request, send_from_directory
    from werkzeug.exceptions import NotFound
    from werkzeug.utils import secure_filename
except Exception:
    print("Missing dependencies, Try pip install pyqrcode flask")
    sys.exit(1)

# disable logging output
logging.getLogger("werkzeug").disabled = True
os.environ["WERKZEUG_RUN_MAIN"] = "true"
os.environ["WERKZEUG_SERVER_FD"] = "1"


app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["UPLOAD_FOLDER"] = os.getcwd()

gport = 9050
gfile = ""
gdirectory = os.getcwd()
ip_address = socket.gethostbyname(socket.gethostname())


@click.group()
def cli():
    pass


@click.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-p", "--port", type=int, default=gport, help="port to use", show_default=True
)
def send(file, port):
    """Serve shared file"""
    click.echo(file)
    global gfile
    global gdirectory
    if file.count("/") > 1:
        gdirectory, gfile = file.rsplit("/", 1)
    else:
        gfile = file

    start_flask("send", port)


@click.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    help="Folder for downloaded files to be saved",
)
@click.option(
    "-p", "--port", type=int, default=gport, help="port to use", show_default=True
)
def receive(directory, port):
    """Receive files"""
    if directory:
        print(directory)
        app.config["UPLOAD_FOLDER"] = directory
    start_flask("receive", port)


cli.add_command(send)
cli.add_command(receive)


def start_flask(command, port):
    url = "http://{}:{}/{}".format(ip_address, port, command)
    qr = pyqrcode.create(url)
    click.echo(qr.terminal(quiet_zone=1))
    click.echo("Link: {}".format(url))
    wsgi.server(eventlet.listen(("0.0.0.0", port)), app)


@app.route("/")
def index():
    return index_tepmlate


@app.route("/send")
def send_():
    try:
        return send_from_directory(gdirectory, gfile, as_attachment=True)
    except NotFound:
        click.echo("File not found, may be wrong path or filename.")
        sys.exit(1)


@app.route("/receive", methods=["GET", "POST"])
def receive_():
    if request.method == "POST":
        if "file" not in request.files:
            return failed_send_template
        files = request.files.getlist("file")
        for file in files:
            if file.filename == "":
                return failed_send_template
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return success_template
    return upload_template


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers["Cache-Control"] = "public, max-age=0"
    return r


index_tepmlate = """
<!doctype html>
<title>pyShare</title>
<h1>pyShare is a very simple script to share files via browser in local networke</h1>
"""

upload_template = """
<html>
<head>
<style>html, body {height: 100%;}.full-height {height: 100%;}.half-height {height: 50%;}.full-width{width:100%;}</style>
</head>
<body>
<title>Send new File</title>
<h1>Send new File</h1>
<form class="full-height" method=post enctype=multipart/form-data>
<div class ="half-height"><input class="full-height full-width" type=file name=file multiple></div>
<div class ="half-height"><input class="full-height full-width" type=submit value=Upload></div>
</form>
</body>
</html>
"""


failed_send_template = """
<html>
<head>
<style>html, body {height: 100%;}.full-height {height: 100%;}.half-height {height: 50%;}.full-width{width:100%;}</style>
</head>
<body>
<title>Send new File</title>
<h1>Sending faile, try again</h1>
<form class="full-height" method=post enctype=multipart/form-data>
<div class ="half-height"><input class="full-height full-width" type=file name=file></div>
<div class ="half-height"><input class="full-height full-width" type=submit value=Upload></div>
</form>
</body>
</html>
"""

success_template = """
<!doctype html>
<title>Sending success</title>
<h1>Sending success</h1>
"""

if __name__ == "__main__":
    cli()
