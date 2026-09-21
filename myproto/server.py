"""MYP/1.0 server: reads headers first, then decodes the body accordingly."""

import argparse
import socket
import threading
import xml.etree.ElementTree as ET

from wire import VERSION, build_message, decode_body, read_message


def handle_client(connection, address):
    with connection:
        stream = connection.makefile("rb")
        message = read_message(stream)
        if message is None:
            return
        start_line, headers, body = message
        print("Request from", address, ":", start_line, headers)

        try:
            data = decode_body(headers, body)
            name = data.get("name", "anonymous")
            reply = build_message(
                "{} 200 OK".format(VERSION),
                headers["content-type"],
                {"message": "Hello, {}!".format(name)},
            )
        except LookupError:
            reply = build_message(
                "{} 415 Unsupported Media Type".format(VERSION),
                "json",
                {"error": "Content-Type missing or not one of json, xml, csv"},
            )
        except (UnicodeDecodeError, ValueError, AttributeError, ET.ParseError) as error:
            reply = build_message(
                "{} 400 Bad Request".format(VERSION),
                "json",
                {"error": "Body does not match declared Content-Type: {}".format(error)},
            )
        connection.sendall(reply)


def serve(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print("MYP/1.0 listening on {}:{}".format(host, port))
        while True:
            connection, address = server_socket.accept()
            threading.Thread(
                target=handle_client, args=(connection, address), daemon=True
            ).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MYP/1.0 demo server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5002)
    arguments = parser.parse_args()
    serve(arguments.host, arguments.port)
