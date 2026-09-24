"""Presentation formats shared by the demo client and server."""

import csv
import io
import json
import pickle
import re
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


HEADER_NAME = re.compile(r"[A-Za-z0-9-]+")
MAX_HEADER_LINES = 32
MAX_LINE_BYTES = 1024
MAX_BODY_BYTES = 1024 * 1024


class FramingError(ValueError):
    """The bytes on the wire do not follow the header + body layout."""


def write_message(format_name, data):
    """Build a full message: headers, blank line, then exactly Content-Length bytes."""
    body = encode(data, format_name)[:-1]
    head = "Content-Type: {}\nContent-Length: {}\n\n".format(format_name, len(body))
    return head.encode("utf-8") + body


def read_message(stream):
    """Read one message from a binary stream. Returns (headers, body) or None if the peer closed."""
    headers = {}
    while True:
        raw = stream.readline(MAX_LINE_BYTES + 1)
        if not raw:
            if headers:
                raise FramingError("Connection closed before the blank line ending the headers")
            return None
        if len(raw) > MAX_LINE_BYTES:
            raise FramingError("Header line too long")
        if not raw.endswith(b"\n"):
            raise FramingError("Connection closed in the middle of a header line")

        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            break
        name, separator, value = line.partition(":")
        if not separator or not HEADER_NAME.fullmatch(name.strip()):
            raise FramingError("Malformed header line: {!r}".format(line[:60]))
        if len(headers) >= MAX_HEADER_LINES:
            raise FramingError("Too many headers")
        headers[name.strip().lower()] = value.strip()

    if not headers:
        raise FramingError("Message has no headers")
    if "content-length" not in headers:
        raise FramingError("Missing Content-Length header")
    try:
        length = int(headers["content-length"])
    except ValueError:
        raise FramingError("Content-Length is not a number") from None
    if not 0 <= length <= MAX_BODY_BYTES:
        raise FramingError("Content-Length out of range (0 to {})".format(MAX_BODY_BYTES))

    body = stream.read(length)
    if len(body) != length:
        raise FramingError("Body is shorter than Content-Length")
    return headers, body
