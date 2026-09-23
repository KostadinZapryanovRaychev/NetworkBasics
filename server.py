"""Tiny TCP server showing application and presentation layers."""

import argparse
import socket
import threading

from protocol import FORMATS, decode, encode
from ip import get_local_ip

HOST = get_local_ip()
PORT = 5001


def application_handle(message):
    """Application layer: decide what the message means."""
    if message.get("type") != "greeting":
        return {"type": "error", "message": "Unknown application message type"}

    name = message.get("name", "anonymous")
    return {
        "type": "greeting_reply",
        "message": "Hello, {}!".format(name),
    }


def handle_client(connection, address):
    with connection:
        print("Connected without authentication:", address)
        stream = connection.makefile("rb")
        header_line = stream.readline().decode("utf-8").strip()
        if not header_line:
            return

        # Header: the client tells us what format is coming next, so the
        # server no longer needs to be started with a matching --format.
        name, _, format_name = header_line.partition(":")
        format_name = format_name.strip()
        if name.strip().lower() != "content-type" or format_name not in FORMATS:
            reply = {
                "type": "protocol_error",
                "message": "Missing or unknown Content-Type header: {!r}".format(header_line),
            }
            print("PROTOCOL FAILURE:", reply["message"])
            connection.sendall(b"Content-Type: json\n" + encode(reply, "json"))
            return

        received = stream.readline()
        try:
            message = decode(received, format_name)
            print("Presentation decoded:", message)
            reply = application_handle(message)
        except (UnicodeDecodeError, ValueError, AttributeError) as error:
            # Report a protocol-level problem, not the parser's internal
            # diagnostics (e.g. "line 1 column 1 (char 0)"), which exposes
            # server implementation details and means nothing to a client
            # that isn't Python.
            reply = {
                "type": "protocol_error",
                "message": "Body does not match declared Content-Type: {}".format(format_name),
            }
            print("PROTOCOL FAILURE:", reply["message"], "-", error)

        header = "Content-Type: {}\n".format(format_name).encode("utf-8")
        connection.sendall(header + encode(reply, format_name))
        print("Application reply sent to", address, ":", reply)


def serve(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(1)
        print("Listening on {}:{}".format(host, port))
        print("WARNING: no authentication, no encryption, and no access control")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_client,
                args=(connection, address),
                daemon=True,
            ).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application/presentation layer demo server")
    parser.add_argument("--host", default=HOST, help="Leave empty for current local ip")
    parser.add_argument("--port", type=int, default=PORT, help="Leave empty for 5001")
    arguments = parser.parse_args()
    print("Format is read from each client's Content-Type header")
    serve(arguments.host, arguments.port)
