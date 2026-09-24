# Application and Presentation Layers in Python

This is a small TCP demonstration. Run the server in one terminal and the client in another.

## Deliberately insecure network demo

The server binds to `0.0.0.0` by default, so it listens on every network interface. It has no authentication, encryption, or access control. Anyone who knows the server's IP address and port can connect and send a message. The server accepts clients concurrently so multiple devices can connect.

On the server device, find its local IP address (see [Find the server's IP address](#find-the-servers-ip-address)) and start:

```bash
python3 server.py --host 0.0.0.0 --port 5001
```

On another device on the same network, run:

```bash
python3 client.py --host 10.10.32.134  --port 5001 --name "Koce"
```

The server prints each connecting device's address and explicitly reports that authentication was not performed. This is for a controlled classroom network only; do not expose this server to the public internet.

## Run it

```bash
python3 server.py
python3 client.py --name Alice
```

The default format is JSON. Every message, in both directions, has this layout:

```text
Content-Type: json
Content-Length: 36
<blank line>
{"type": "greeting", "name": "Koce"}
```

- **Headers** are `Name: value` lines that describe the message. The blank line ends them. The server ignores headers it does not know, so new ones can be added later without breaking old clients.
- **`Content-Type`** names the format, so the server does not need a matching `--format` flag or a restart.
- **`Content-Length`** is the size of the body in **bytes** (not characters, so `Коце` counts 8). The receiver reads exactly that many bytes, which lets a body contain newlines and lets the receiver notice a truncated message.

Leave the same server running and switch formats on the client alone:

```bash
python3 client.py --format xml --name Alice
python3 client.py --format csv --name Alice
python3 client.py --format urlencoded --name Alice
```

XML, CSV and urlencoded (`type=greeting&name=Alice`, the same encoding HTML forms use) are presentation formats too; the application message remains the same greeting.

For a Python-only experiment, use `--format pickle`:

```bash
python3 client.py --format pickle --name Alice
```

Pickle can serialize a Python object and another Python program can restore it, but a .NET receiver does not understand Python pickle. It is therefore not a good cross-language presentation format, and untrusted pickle data must never be loaded because it can execute code. JSON is useful here because Python and .NET both have safe JSON libraries and can agree on the same representation.

Expected normal result:

```text
NORMAL MODE: JSON presentation layer enabled
Reply headers: {'content-type': 'json', 'content-length': '54'}
Server reply: {'type': 'greeting_reply', 'message': 'Hello, Alice!'}
```

## Remove the presentation layer

Leave the server running and execute:

```bash
python3 client.py --name Alice --remove-presentation
```

The client now sends this instead of headers and a body:

```text
{'type': 'greeting', 'name': 'Alice'}
```

That is Python's `repr()` format, with no headers in front of it. The server always expects header lines first, and a header name may only contain letters, digits and `-`, so it rejects this line at once, reports `PROTOCOL FAILURE`, and returns a `protocol_error` reply (`Malformed message: Malformed header line: ...`). The application layer never gets a usable message. Because the server reads the format from the header instead of a flag you set by hand, the server and client no longer need to be started with the same `--format`; only broken framing, a missing or unrecognized `Content-Type`, or a body that does not match it causes a failure.

The server also protects itself: it waits at most 10 seconds for a client, limits header size and body size (1 MB), and answers every malformed message with a `protocol_error` instead of crashing. Its error text describes the protocol problem, not Python's parser internals.

## Send an unknown format

The clients only offer formats the server knows, so to see the server reject an unknown protocol, send the bytes by hand with `nc` (netcat, available on macOS and Linux). This declares a `yaml` body, which the server does not support:

```bash
printf 'Content-Type: yaml\nContent-Length: 2\n\n{}' | nc 127.0.0.1 5001
```

The framing is valid (headers, blank line, 2 bytes of body), but the server has no decoder for `yaml`, so it replies:

```text
Content-Type: json
Content-Length: 87

{"type": "protocol_error", "message": "Missing or unknown Content-Type header: 'yaml'"}
```

Replace `127.0.0.1` with the server's IP to test from another device. The known formats are `json`, `xml`, `csv`, `urlencoded` and `pickle`.

## Find the server's IP address

Run one of these **on the server device** (the one running `server.py`) and use the result as `--host` in the clients. Look for a private address such as `192.168.x.x`, `10.x.x.x` or `172.16.x.x`-`172.31.x.x`. A public address will not work on the classroom network.

| OS      | Command                  | What to read                                               |
| ------- | ------------------------ | ---------------------------------------------------------- |
| macOS   | `ipconfig getifaddr en0` | Prints the IP directly. Try `en1` if `en0` prints nothing. |
| Windows | `ipconfig`               | The `IPv4 Address` under your Wi-Fi or Ethernet adapter.   |
| Linux   | `hostname -I`            | The first address printed. `ip -4 addr` shows more detail. |

On Windows, Python is usually started with `python` or `py` instead of `python3`. If clients cannot connect, allow Python through the server device's firewall. In the examples below, `10.10.32.241` stands for that IP.

## Clients in other languages

Every client below does the same thing as `client.py`: it sends `Content-Type` and `Content-Length` headers, a blank line and a greeting body to the Python server on port 5001, and takes `--format json` (default) or `--format urlencoded`. Each also has a `--broken` option that skips both the headers and serialization. Start the server first on the server device:

```bash
python3 server.py --host 0.0.0.0 --port 5001
```

Then run a client from the project folder (`NetworkBasics/`), replacing `10.10.32.241` with the server's IP.

| Language | Needs        | Run from         | Command                                                                      |
| -------- | ------------ | ---------------- | ---------------------------------------------------------------------------- |
| Python   | Python 3     | project root     | `python3 client.py --host 10.10.32.241 --port 5001 --name "Koce"`            |
| Node.js  | Node.js      | project root     | `node node-client/client.js --host 10.10.32.241 --port 5001 --name "Koce"`   |
| Java     | JDK 11+      | project root     | `java java-client/Client.java --host 10.10.32.241 --port 5001 --name "Koce"` |
| Go       | Go           | `go-client/`     | `go run main.go --host 10.10.32.241 --port 5001 --name "Koce"`               |
| C#       | .NET SDK     | `csharp-client/` | `dotnet run -- --host 10.10.32.241 --port 5001 --name "Koce"`                |
| Rust     | Rust (cargo) | `rust-client/`   | `cargo run -- --host 10.10.32.241 --port 5001 --name "Koce"`                 |

Expected result for any of them: the reply headers, then a body such as `{"type": "greeting_reply", "message": "Hello, Koce!"}`. Names with quotes or non-ASCII letters (for example `--name "Коце"`) work too, because each client escapes and counts bytes correctly.

Add `--format urlencoded` to send `type=greeting&name=Koce` instead, on the same running server, no restart needed:

```bash
node node-client/client.js --host 10.10.32.241 --port 5001 --name "Koce" --format urlencoded
java java-client/Client.java --host 10.10.32.241 --port 5001 --name "Koce" --format urlencoded
(cd go-client && go run main.go --host 10.10.32.241 --port 5001 --name "Koce" --format urlencoded)
(cd csharp-client && dotnet run -- --host 10.10.32.241 --port 5001 --name "Koce" --format urlencoded)
(cd rust-client && cargo run -- --host 10.10.32.241 --port 5001 --name "Koce" --format urlencoded)
```

Add `--broken` to see the failure. Each language sends its own native representation instead of a header and body:

| Language | `--broken` sends                                                                            |
| -------- | ------------------------------------------------------------------------------------------- |
| Python   | `{'type': 'greeting', 'name': 'Koce'}` (uses `--remove-presentation` instead of `--broken`) |
| Node.js  | `[object Object]`, the plain object turned into text                                        |
| Java     | `Client$Greeting@5e5d171f`, the default `toString()`                                        |
| Go       | `{Type:greeting Name:Koce}`                                                                 |
| C#       | `Greeting { Type = greeting, Name = Koce }`                                                 |
| Rust     | `Greeting { msg_type: "greeting", name: "Koce" }`                                           |

For example:

```bash
node node-client/client.js --host 10.10.32.241 --port 5001 --name "Koce" --broken
```

The server expects header lines first, so it sees this text instead and replies `protocol_error: Malformed message: Malformed header line: ...`. In each case the bytes arrive over TCP, but the receiver cannot turn them back into data because each language's native representation is private to that language. Serialization to a shared format, declared with a header, is what makes them interoperable.

If you see `ECONNREFUSED` or `Connection refused`, the server is not running or the IP is wrong.

## MYP/1.0: a protocol with headers

The [myproto/](myproto/) folder holds a small HTTP-like protocol that fixes the problem above. The client declares the format before sending the body, so the server no longer has to guess:

```text
GREET MYP/1.0
Content-Type: json
Content-Length: 36

{"type": "greeting", "name": "Koce"}
```

It uses its own server, on port 5002:

```bash
python3 myproto/server.py --host 0.0.0.0 --port 5002
python3 myproto/client.py --host 10.10.32.241 --port 5002 --name "Koce"
```

Try these to see how the server reacts to bad headers:

```bash
python3 myproto/client.py --host 10.10.32.241 --port 5002 --name "Koce" --format xml
python3 myproto/client.py --host 10.10.32.241 --port 5002 --name "Koce" --lie
python3 myproto/client.py --host 10.10.32.241 --port 5002 --name "Koce" --header-type yaml
```

- `--format xml` sends honest XML and gets `200 OK`.
- `--lie` declares XML but sends JSON, and gets `400 Bad Request`.
- `--header-type yaml` declares a type the server does not know, and gets `415 Unsupported Media Type`.

## What each layer does

- **Transport layer:** TCP moves bytes between the two devices. It does not know what the bytes mean.
- **Presentation layer:** UTF-8 and JSON define how the data is represented on the wire. Both sides must agree on this format.
- **Application layer:** `greeting` and `greeting_reply` define the meaning and behavior of the messages.

The `--remove-presentation` option demonstrates the boundary: the application still creates a greeting, and TCP still connects, but the receiver cannot interpret the bytes. In a real internet deployment, replace `127.0.0.1` with the server device's reachable IP address, open the selected TCP port in its firewall, and consider TLS for encryption and authentication.
