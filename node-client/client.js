// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) only understands the wire formats defined
// in protocol.py (JSON, XML, CSV, pickle). A plain JavaScript object turns
// into "[object Object]" when sent without serializing, so sending it "as is"
// demonstrates the same point as client.py's --broken flag, the C# client's
// --broken flag, and the Rust client's --broken flag, but from Node this
// time. No dependencies: uses only Node's built-in net module.

const net = require("net");

function parseArgs(argv) {
  const options = {
    host: "127.0.0.1",
    port: 5001,
    name: "Student",
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
      case "--broken":
        options.broken = true;
        break;
    }
  }
  return options;
}

const { host, port, name, broken } = parseArgs(process.argv.slice(2));

const greeting = { type: "greeting", name };

let wireMessage;
if (broken) {
  // Deliberately skip JSON and hand the plain object to the socket layer.
  // A socket only carries bytes/strings, so the object gets coerced to
  // its default string form: "[object Object]" (the classic JS mistake).
  console.log("BROKEN MODE: presentation layer removed");
  console.log("Sending plain JavaScript object:", greeting);
  wireMessage = greeting + "\n";
  console.log("What actually goes on the wire:", JSON.stringify(wireMessage));
} else {
  // Presentation layer: application data -> agreed JSON wire format.
  const json = JSON.stringify(greeting);
  console.log("NORMAL MODE: JSON presentation layer enabled");
  console.log("Sending JSON:", json);
  wireMessage = json + "\n";
}

const socket = net.createConnection({ host, port }, () => {
  socket.write(wireMessage);
});

let buffer = "";
socket.on("data", (chunk) => {
  buffer += chunk.toString("utf8");
  const newlineIndex = buffer.indexOf("\n");
  if (newlineIndex === -1) {
    return;
  }
  const replyLine = buffer.slice(0, newlineIndex);
  console.log("Raw server reply:", replyLine);
  socket.end();
});

socket.on("error", (error) => {
  console.error("Connection error:", error.message);
});
