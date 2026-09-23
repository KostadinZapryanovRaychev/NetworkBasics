// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) reads a Content-Type header line before the
// body, so the format can change per request without restarting the server.
// Java's default Object.toString() (ClassName@hashcode) is none of the
// formats it understands, and skips the header entirely, so sending it
// "as is" demonstrates the same point as client.py's --remove-presentation
// flag, but even more dramatically. No dependencies: plain JDK only, run
// directly with `java Client.java`.

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

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

    static String encodeBody(String format, Greeting greeting) {
        if (format.equals("json")) {
            return String.format("{\"type\": \"%s\", \"name\": \"%s\"}", greeting.type, greeting.name);
        }
        if (format.equals("urlencoded")) {
            String type = URLEncoder.encode(greeting.type, StandardCharsets.UTF_8);
            String name = URLEncoder.encode(greeting.name, StandardCharsets.UTF_8);
            return "type=" + type + "&name=" + name;
        }
        throw new IllegalArgumentException("Unsupported format: " + format);
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

        String wireMessage;
        if (broken) {
            // Deliberately skip both the header and JSON. This is Java's
            // internal object representation, not the shared wire format
            // the server expects, and there is no Content-Type line either.
            String raw = greeting.toString();
            System.out.println("BROKEN MODE: presentation layer removed");
            System.out.println("Sending raw Java representation: " + raw);
            wireMessage = raw + "\n";
        } else {
            // Presentation layer: application data -> agreed wire format,
            // with a Content-Type header so the server knows which one
            // without being told in advance.
            String body = encodeBody(format, greeting);
            System.out.println("NORMAL MODE: " + format.toUpperCase() + " presentation layer enabled");
            System.out.println("Sending body: " + body);
            wireMessage = "Content-Type: " + format + "\n" + body + "\n";
        }

        try (Socket socket = new Socket(host, port)) {
            OutputStream out = socket.getOutputStream();
            out.write(wireMessage.getBytes(StandardCharsets.UTF_8));
            out.flush();

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            String replyHeader = reader.readLine();
            String replyBody = reader.readLine();

            if (replyHeader == null) {
                System.out.println("No reply from server.");
                return;
            }
            System.out.println("Reply header: " + replyHeader);
            System.out.println("Reply body: " + replyBody);
        }
    }
}
