// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) reads a Content-Type header line before the
// body, so the format can change per request without restarting the server.
// A plain JavaScript object turns into "[object Object]" when sent without
// serializing and with no header, so sending it "as is" demonstrates the
// same point as client.py's --remove-presentation flag, but from Node this
// time. No dependencies: uses only Node's built-in net module.

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
  // Deliberately skip both the header and serialization, and hand the
  // plain object to the socket layer. A socket only carries bytes/strings,
  // so the object gets coerced to its default string form: "[object Object]"
  // (the classic JS mistake). The server expects a header line first, so
  // it never even gets to the point of parsing this as a body.
  console.log("BROKEN MODE: presentation layer removed");
  console.log("Sending plain JavaScript object:", greeting);
  wireMessage = greeting + "\n";
  console.log("What actually goes on the wire:", JSON.stringify(wireMessage));
} else {
  // Presentation layer: application data -> agreed wire format, with a
  // Content-Type header so the server knows which one without being told
  // in advance.
  const body = encodeBody(format, greeting);
  console.log("NORMAL MODE: " + format.toUpperCase() + " presentation layer enabled");
  console.log("Sending body:", body);
  wireMessage = "Content-Type: " + format + "\n" + body + "\n";
}

const socket = net.createConnection({ host, port }, () => {
  socket.write(wireMessage);
});

let buffer = "";
let sawHeader = false;
socket.on("data", (chunk) => {
  buffer += chunk.toString("utf8");
  if (!sawHeader) {
    const headerEnd = buffer.indexOf("\n");
    if (headerEnd === -1) {
      return;
    }
    console.log("Reply header:", buffer.slice(0, headerEnd));
    buffer = buffer.slice(headerEnd + 1);
    sawHeader = true;
  }
  const bodyEnd = buffer.indexOf("\n");
  if (bodyEnd === -1) {
    return;
  }
  console.log("Reply body:", buffer.slice(0, bodyEnd));
  socket.end();
});

socket.on("error", (error) => {
  console.error("Connection error:", error.message);
});
