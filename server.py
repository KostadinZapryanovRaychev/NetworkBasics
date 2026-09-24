"""Tiny TCP server showing application and presentation layers."""

import argparse
import socket
import pickle
import threading
import xml.etree.ElementTree as ET

from protocol import FORMATS, FramingError, decode, read_message, write_message
from ip import get_local_ip

HOST = get_local_ip()
PORT = 5001
CLIENT_TIMEOUT_SECONDS = 10


def application_handle(message):
    """Application layer: decide what the message means."""
    if message.get("type") != "greeting":
        return {"type": "error", "message": "Unknown application message type"}

    name = message.get("name", "anonymous")
    return {
        "type": "greeting_reply",
        "message": "Hello, {}!".format(name),
    }


def reply_error(connection, message):
    print("PROTOCOL FAILURE:", message)
    connection.sendall(write_message("json", {"type": "protocol_error", "message": message}))


def handle_client(connection, address):
    with connection:
        connection.settimeout(CLIENT_TIMEOUT_SECONDS)
        print("Connected without authentication:", address)
        try:
            received = read_message(connection.makefile("rb"))
            if received is None:
                return
            headers, body = received

            format_name = headers.get("content-type", "")
            if format_name not in FORMATS:
                reply_error(connection, "Missing or unknown Content-Type header: {!r}".format(format_name[:40]))
                return

            try:
                message = decode(body, format_name)
                print("Presentation decoded:", message)
                reply = application_handle(message)
            except (UnicodeDecodeError, ValueError, AttributeError, TypeError, ET.ParseError, pickle.UnpicklingError) as error:
                # Log the parser's own wording locally; clients only get a
                # protocol-level message that does not depend on Python.
                print("Decode detail:", error)
                reply_error(connection, "Body does not match declared Content-Type: {}".format(format_name))
                return

            connection.sendall(write_message(format_name, reply))
            print("Application reply sent to", address, ":", reply)
        except FramingError as error:
            reply_error(connection, "Malformed message: {}".format(error))
        except (socket.timeout, ConnectionError) as error:
            print("Connection problem with", address, ":", error)


def serve(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(50)
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
    print("Each message: headers, blank line, then Content-Length bytes of body")
    serve(arguments.host, arguments.port)
