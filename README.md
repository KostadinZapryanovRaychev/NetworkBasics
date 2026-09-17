# Application and Presentation Layers in Python

This is a small TCP demonstration. Run the server in one terminal and the client in another.

## Deliberately insecure network demo

The server binds to `0.0.0.0` by default, so it listens on every network interface. It has no authentication, encryption, or access control. Anyone who knows the server's IP address and port can connect and send a message. The server accepts clients concurrently so multiple devices can connect.

On the server device, find its local IP address and start:

```bash
python3 server.py --host 0.0.0.0 --port 5001
```

On another device on the same network, run:

```bash
python3 client.py --host 10.10.32.241  --port 5001 --name "Koce"
```

The server prints each connecting device's address and explicitly reports that authentication was not performed. This is for a controlled classroom network only; do not expose this server to the public internet.

## Run it

```bash
python3 server.py
python3 client.py --name Alice
```

The default format is JSON. To use another presentation format, start both sides with the same choice:

```bash
python3 server.py --format xml
python3 client.py --format xml --name Alice
```

You can also use `--format csv`. XML and CSV are presentation formats too; the application message remains the same greeting.

For a Python-only experiment, use `--format pickle`:

```bash
python3 server.py --format pickle
python3 client.py --format pickle --name Alice
```

Pickle can serialize a Python object and another Python program can restore it, but a .NET receiver does not understand Python pickle. It is therefore not a good cross-language presentation format, and untrusted pickle data must never be loaded because it can execute code. JSON is useful here because Python and .NET both have safe JSON libraries and can agree on the same representation.

Expected normal result:

```text
NORMAL MODE: JSON presentation layer enabled
Server reply: {'type': 'greeting_reply', 'message': 'Hello, Alice!'}
```

## Remove the presentation layer

Leave the server running and execute:

```bash
python3 client.py --name Alice --remove-presentation
```

The client now sends this instead of JSON:

```text
{'type': 'greeting', 'name': 'Alice'}
```

That is Python's `repr()` format. It uses single quotes, so it is not valid JSON. The server cannot decode it, reports `PROTOCOL FAILURE`, and returns a `protocol_error` message. The application layer never gets a usable message. The same failure happens if the server and client choose different formats.

## What each layer does

- **Transport layer:** TCP moves bytes between the two devices. It does not know what the bytes mean.
- **Presentation layer:** UTF-8 and JSON define how the data is represented on the wire. Both sides must agree on this format.
- **Application layer:** `greeting` and `greeting_reply` define the meaning and behavior of the messages.

The `--remove-presentation` option demonstrates the boundary: the application still creates a greeting, and TCP still connects, but the receiver cannot interpret the bytes. In a real internet deployment, replace `127.0.0.1` with the server device's reachable IP address, open the selected TCP port in its firewall, and consider TLS for encryption and authentication.

ipconfig getifaddr en0
