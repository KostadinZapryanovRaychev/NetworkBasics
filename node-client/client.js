// Tiny TCP client showing why a shared presentation format is needed.
//
// Every message is: headers (Name: value lines), a blank line, then exactly
// Content-Length bytes of body. The Python server reads the Content-Type
// header to pick the decoder, so the format can change per request without
// restarting it. A plain JavaScript object turns into "[object Object]" when
// sent without serializing and without headers, which demonstrates the same
// point as client.py's --remove-presentation flag, but from Node this time.
// No dependencies: uses only Node's built-in net module.

const net = require("net");

function parseArgs(argv) {
  const options = {
    host: "127.0.0.1",
    port: 5001,
    name: "Student",
    format: "json",
    broken: false,
  };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--host":
        options.host = argv[++i];
        break;
      case "--port":
        options.port = parseInt(argv[++i], 10);
        break;
      case "--name":
        options.name = argv[++i];
        break;
      case "--format":
        options.format = argv[++i];
        break;
      case "--broken":
        options.broken = true;
        break;
    }
  }
  return options;
}

function encodeBody(format, greeting) {
  if (format === "json") {
    return JSON.stringify(greeting);
  }
  if (format === "urlencoded") {
    return new URLSearchParams(greeting).toString();
  }
  throw new Error("Unsupported format: " + format);
}

const { host, port, name, format, broken } = parseArgs(process.argv.slice(2));

const greeting = { type: "greeting", name };

let wireMessage;
if (broken) {
  // Deliberately skip the headers and serialization, and hand the plain
  // object to the socket layer. A socket only carries bytes/strings, so the
  // object gets coerced to its default string form: "[object Object]" (the
  // classic JS mistake). The server expects headers first, so it rejects
  // this line as a malformed header.
  console.log("BROKEN MODE: presentation layer removed");
  console.log("Sending plain JavaScript object:", greeting);
  wireMessage = Buffer.from(greeting + "\n", "utf8");
  console.log("What actually goes on the wire:", JSON.stringify(String(wireMessage)));
} else {
  // Presentation layer: application data -> agreed wire format. The header
  // names the format and Content-Length counts BYTES, not characters.
  const body = Buffer.from(encodeBody(format, greeting), "utf8");
  const head = `Content-Type: ${format}\nContent-Length: ${body.length}\n\n`;
  console.log("NORMAL MODE: " + format.toUpperCase() + " presentation layer enabled");
  console.log("Sending body:", body.toString("utf8"));
  wireMessage = Buffer.concat([Buffer.from(head, "utf8"), body]);
}

const socket = net.createConnection({ host, port }, () => {
  socket.write(wireMessage);
});
socket.setTimeout(10000, () => {
  console.error("Timed out waiting for the server");
  socket.destroy();
});

let received = Buffer.alloc(0);
let finished = false;

function tryFinish() {
  const headerEnd = received.indexOf("\n\n");
  if (headerEnd === -1) {
    return;
  }
  const headerText = received.subarray(0, headerEnd).toString("utf8");
  const headers = {};
  for (const line of headerText.split("\n")) {
    const colon = line.indexOf(":");
    if (colon > 0) {
      headers[line.slice(0, colon).trim().toLowerCase()] = line.slice(colon + 1).trim();
    }
  }
  const length = parseInt(headers["content-length"], 10);
  if (Number.isNaN(length)) {
    console.error("Reply has no valid Content-Length");
    finished = true;
    socket.end();
    return;
  }
  const bodyStart = headerEnd + 2;
  if (received.length < bodyStart + length) {
    return;
  }
  console.log("Reply headers:", headers);
  console.log("Reply body:", received.subarray(bodyStart, bodyStart + length).toString("utf8"));
  finished = true;
  socket.end();
}

socket.on("data", (chunk) => {
  received = Buffer.concat([received, chunk]);
  if (!finished) {
    tryFinish();
  }
});

socket.on("end", () => {
  if (!finished) {
    console.error("Server closed the connection before a full reply arrived");
  }
});

socket.on("error", (error) => {
  console.error("Connection error:", error.message);
});
