// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) only understands the wire formats defined
// in protocol.py (JSON, XML, CSV, pickle). Node's own util.inspect()
// representation of an object is none of those, so sending it "as is"
// demonstrates the same point as client.py's --broken flag, the C# client's
// --broken flag, and the Rust client's --broken flag, but from Node this
// time. No dependencies: uses only Node's built-in net and util modules.

const net = require("net");
const util = require("util");

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
  // Deliberately skip JSON. This is Node's internal object
  // representation, not the shared wire format the server expects.
  const raw = util.inspect(greeting);
  console.log("BROKEN MODE: presentation layer removed");
  console.log("Sending raw Node representation:", raw);
  wireMessage = raw + "\n";
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
