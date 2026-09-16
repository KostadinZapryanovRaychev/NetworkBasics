"""Tiny TCP server showing application and presentation layers."""

import argparse
import socket
import threading

from protocol import FORMATS, decode, encode

HOST = "0.0.0.0"
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


def handle_client(connection, address, format_name):
    with connection:
        print("Connected without authentication:", address)
        received = connection.makefile("rb").readline()
        if not received:
            return

        try:
            message = decode(received, format_name)
            print("Presentation decoded:", message)
            reply = application_handle(message)
            connection.sendall(encode(reply, format_name))
            print("Application reply sent to", address, ":", reply)
        except (UnicodeDecodeError, ValueError, AttributeError) as error:
            error_message = {
                "type": "protocol_error",
                "message": "Presentation layer could not decode the message: {}".format(error),
            }
            print("PROTOCOL FAILURE:", error_message["message"])
            connection.sendall(encode(error_message, format_name))


def serve(host, port, format_name):
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
                args=(connection, address, format_name),
                daemon=True,
            ).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application/presentation layer demo server")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--format", choices=FORMATS, default="json")
    arguments = parser.parse_args()
    print("Presentation format:", arguments.format)
    serve(arguments.host, arguments.port, arguments.format)
