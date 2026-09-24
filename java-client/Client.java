// Tiny TCP client showing why a shared presentation format is needed.
//
// Every message is: headers (Name: value lines), a blank line, then exactly
// Content-Length bytes of body. The Python server reads the Content-Type
// header to pick the decoder, so the format can change per request without
// restarting it. Java's default Object.toString() (ClassName@hashcode) is
// none of the formats it understands and has no headers, so sending it
// "as is" demonstrates the same point as client.py's --remove-presentation
// flag, but even more dramatically. No dependencies: plain JDK only, run
// directly with `java Client.java` (JDK 11+).

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public class Client {

    static class Greeting {
        String type;
        String name;

        Greeting(String type, String name) {
            this.type = type;
            this.name = name;
        }
        // Deliberately no toString() override, so the default
        // Object.toString() (ClassName@hashcode) is used in broken mode.
    }

    static String jsonString(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            switch (c) {
                case '"': out.append("\\\""); break;
                case '\\': out.append("\\\\"); break;
                case '\n': out.append("\\n"); break;
                case '\r': out.append("\\r"); break;
                case '\t': out.append("\\t"); break;
                default:
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
            }
        }
        return out.append('"').toString();
    }

    static String encodeBody(String format, Greeting greeting) {
        if (format.equals("json")) {
            return "{\"type\": " + jsonString(greeting.type) + ", \"name\": " + jsonString(greeting.name) + "}";
        }
        if (format.equals("urlencoded")) {
            String type = URLEncoder.encode(greeting.type, StandardCharsets.UTF_8);
            String name = URLEncoder.encode(greeting.name, StandardCharsets.UTF_8);
            return "type=" + type + "&name=" + name;
        }
        throw new IllegalArgumentException("Unsupported format: " + format);
    }

    // Reads one line as UTF-8 up to '\n' (without it). Returns null at end of stream.
    static String readLine(InputStream in) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        int b;
        while ((b = in.read()) != -1) {
            if (b == '\n') {
                return line.toString(StandardCharsets.UTF_8);
            }
            line.write(b);
        }
        return line.size() == 0 ? null : line.toString(StandardCharsets.UTF_8);
    }

    public static void main(String[] args) throws Exception {
        String host = "127.0.0.1";
        int port = 5001;
        String name = "Student";
        String format = "json";
        boolean broken = false;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--host":
                    host = args[++i];
                    break;
                case "--port":
                    port = Integer.parseInt(args[++i]);
                    break;
                case "--name":
                    name = args[++i];
                    break;
                case "--format":
                    format = args[++i];
                    break;
                case "--broken":
                    broken = true;
                    break;
            }
        }

        Greeting greeting = new Greeting("greeting", name);

        byte[] wireMessage;
        if (broken) {
            // Deliberately skip the headers and serialization. This is Java's
            // internal object representation, not the shared wire format the
            // server expects.
            String raw = greeting.toString();
            System.out.println("BROKEN MODE: presentation layer removed");
            System.out.println("Sending raw Java representation: " + raw);
            wireMessage = (raw + "\n").getBytes(StandardCharsets.UTF_8);
        } else {
            // Presentation layer: application data -> agreed wire format. The
            // header names the format and Content-Length counts BYTES.
            String body = encodeBody(format, greeting);
            byte[] bodyBytes = body.getBytes(StandardCharsets.UTF_8);
            String head = "Content-Type: " + format + "\nContent-Length: " + bodyBytes.length + "\n\n";
            System.out.println("NORMAL MODE: " + format.toUpperCase() + " presentation layer enabled");
            System.out.println("Sending body: " + body);
            ByteArrayOutputStream message = new ByteArrayOutputStream();
            message.write(head.getBytes(StandardCharsets.UTF_8));
            message.write(bodyBytes);
            wireMessage = message.toByteArray();
        }

        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 10000);
            socket.setSoTimeout(10000);
            OutputStream out = socket.getOutputStream();
            out.write(wireMessage);
            out.flush();

            InputStream in = socket.getInputStream();
            Map<String, String> headers = new HashMap<>();
            String line;
            while ((line = readLine(in)) != null && !line.isBlank()) {
                int colon = line.indexOf(':');
                if (colon > 0) {
                    headers.put(line.substring(0, colon).trim().toLowerCase(), line.substring(colon + 1).trim());
                }
            }
            if (headers.isEmpty()) {
                System.out.println("No reply from server.");
                return;
            }
            String lengthText = headers.get("content-length");
            if (lengthText == null) {
                System.out.println("Reply has no Content-Length");
                return;
            }
            byte[] replyBody = in.readNBytes(Integer.parseInt(lengthText));
            System.out.println("Reply headers: " + headers);
            System.out.println("Reply body: " + new String(replyBody, StandardCharsets.UTF_8));
        }
    }
}
