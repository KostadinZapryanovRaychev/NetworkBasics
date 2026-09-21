"""MYP/1.0: a tiny HTTP-like text protocol with headers.

Message layout (request and response share it):

    <start line>\n
    Header-Name: value\n
    Header-Name: value\n
    \n
    <body, exactly Content-Length bytes>
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from protocol import decode, encode  # noqa: E402

VERSION = "MYP/1.0"
FORMATS = ("json", "xml", "csv")


def build_message(start_line, format_name, data):
    body = encode(data, format_name).rstrip(b"\n")
    head = "{}\nContent-Type: {}\nContent-Length: {}\n\n".format(
        start_line, format_name, len(body)
    )
    return head.encode("utf-8") + body


def read_message(stream):
    """Return (start_line, headers, body) or None if the peer closed."""
    start_line = stream.readline().decode("utf-8").strip()
    if not start_line:
        return None

    headers = {}
    while True:
        line = stream.readline().decode("utf-8").strip()
        if not line:
            break
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    body = stream.read(length) if length else b""
    return start_line, headers, body


def decode_body(headers, body):
    format_name = headers.get("content-type", "")
    if format_name not in FORMATS:
        raise LookupError(format_name)
    return decode(body, format_name)
