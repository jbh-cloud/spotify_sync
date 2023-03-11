#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()

print("Content-Type: text/html")
print()

print("<html><head><title>Python WebShell</title></head>")
print("<body><h1>Python WebShell</h1>")

form = cgi.FieldStorage()

if "cmd" in form:
    cmd = form["cmd"].value
    if cmd.startswith("echo "):
        output = cmd[5:]
        print("<p><b>Command:</b> {}</p>".format(cmd))
        print("<p><b>Output:</b></p>")
        print("<pre>{}</pre>".format(output))
    else:
        print("<p>Command not allowed.</p>")
else:
    print("<p>No command entered.</p>")

print("</body></html>")