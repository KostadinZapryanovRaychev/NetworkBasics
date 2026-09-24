"""Tiny TCP client showing valid and broken presentation formats."""

import argparse
import socket

from protocol import FORMATS, FramingError, decode, read_message, write_message


def application_message(name):
    """Application layer: create a meaningful greeting."""
    return {"type": "greeting", "name": name}


def main(host, port, name, format_name, remove_presentation):
    message = application_message(name)

    if remove_presentation:
        # Deliberately skip the headers and serialization. This is Python's
        # internal representation, not the shared wire format the server expects.
        wire_message = (repr(message) + "\n").encode("utf-8")
        print("BROKEN MODE: presentation layer removed")
    else:
        wire_message = write_message(format_name, message)
        print("NORMAL MODE: {} presentation layer enabled".format(format_name.upper()))

    with socket.create_connection((host, port), timeout=10) as connection:
        connection.sendall(wire_message)
        try:
            received = read_message(connection.makefile("rb"))
        except FramingError as error:
            print("CLIENT FRAMING FAILURE:", error)
            return

    if received is None:
        print("No reply from server.")
        return

    headers, body = received
    print("Reply headers:", headers)
    try:
        print("Server reply:", decode(body, headers.get("content-type", "")))
    except (UnicodeDecodeError, ValueError) as error:
        print("CLIENT PRESENTATION FAILURE:", error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application/presentation layer demo client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--name", default="Student")
    parser.add_argument("--format", choices=FORMATS, default="json")
    parser.add_argument(
        "--remove-presentation",
        action="store_true",
        help="send Python repr instead of the agreed JSON wire format",
    )
    arguments = parser.parse_args()
    main(
        arguments.host,
        arguments.port,
        arguments.name,
        arguments.format,
        arguments.remove_presentation,
    )
