"""MYP/1.0 client. --lie sends a JSON body while declaring it as XML."""

import argparse
import socket

from wire import FORMATS, VERSION, build_message, read_message


def main(host, port, name, format_name, lie, header_type):
    request = build_message(
        "GREET {}".format(VERSION), format_name, {"type": "greeting", "name": name}
    )
    if lie:
        request = request.replace(
            "Content-Type: {}".format(format_name).encode(), b"Content-Type: xml", 1
        )
    if header_type is not None:
        request = request.replace(
            "Content-Type: {}".format(format_name).encode(),
            "Content-Type: {}".format(header_type).encode(),
            1,
        )

    with socket.create_connection((host, port)) as connection:
        connection.sendall(request)
        print("Sent:\n" + request.decode("utf-8"))
        reply = read_message(connection.makefile("rb"))

    start_line, headers, body = reply
    print("Reply:", start_line, headers)
    print("Body:", body.decode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MYP/1.0 demo client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    parser.add_argument("--name", default="Student")
    parser.add_argument("--format", choices=FORMATS, default="json")
    parser.add_argument("--lie", action="store_true", help="declare xml but send the real format")
    parser.add_argument("--header-type", help="override Content-Type, e.g. yaml")
    arguments = parser.parse_args()
    main(arguments.host, arguments.port, arguments.name, arguments.format,
         arguments.lie, arguments.header_type)
