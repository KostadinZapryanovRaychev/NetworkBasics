"""Presentation formats shared by the demo client and server."""

import csv
import io
import json
import pickle
import urllib.parse
import xml.etree.ElementTree as ET

FORMATS = ("json", "xml", "csv", "pickle", "urlencoded")


def encode(message, format_name):
    """Presentation layer: application data -> agreed wire bytes."""
    if format_name == "json":
        text = json.dumps(message, ensure_ascii=False)
        return (text + "\n").encode("utf-8")
    if format_name == "pickle":
        # Educational Python-only format; never load untrusted pickle data.
        return pickle.dumps(message) + b"\n"
    elif format_name == "urlencoded":
        # Same content type HTML forms use: application/x-www-form-urlencoded.
        text = urllib.parse.urlencode(message)
    elif format_name == "xml":
        root = ET.Element("message")
        for key, value in message.items():
            element = ET.SubElement(root, key)
            element.text = str(value)
        text = ET.tostring(root, encoding="unicode")
    elif format_name == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(message.keys())
        writer.writerow(message.values())
        text = output.getvalue().rstrip("\r\n")
    else:
        raise ValueError("Unsupported format: {}".format(format_name))
    return (text + "\n").encode("utf-8")


def decode(line, format_name):
    """Presentation layer: agreed wire bytes -> application data."""
    if format_name == "pickle":
        return pickle.loads(line.rstrip(b"\r\n"))

    text = line.decode("utf-8").strip()
    if format_name == "json":
        return json.loads(text)
    if format_name == "xml":
        root = ET.fromstring(text)
        return {element.tag: element.text or "" for element in root}
    if format_name == "csv":
        rows = list(csv.DictReader(io.StringIO(text)))
        if len(rows) != 1:
            raise ValueError("CSV message must contain one data row")
        return rows[0]
    if format_name == "urlencoded":
        pairs = urllib.parse.parse_qsl(text, strict_parsing=True)
        return dict(pairs)
    raise ValueError("Unsupported format: {}".format(format_name))
