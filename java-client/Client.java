// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) only understands the wire formats defined
// in protocol.py (JSON, XML, CSV, pickle). Java's default Object.toString()
// (ClassName@hashcode) is none of those - it does not even carry the
// object's field values - so sending it "as is" demonstrates the same
// point as the other clients' --broken flag, but even more dramatically.
// No dependencies: plain JDK only, run directly with `java Client.java`.

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
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

    public static void main(String[] args) throws Exception {
        String host = "127.0.0.1";
        int port = 5001;
        String name = "Student";
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
                case "--broken":
                    broken = true;
                    break;
            }
        }

        Greeting greeting = new Greeting("greeting", name);

        String wireMessage;
        if (broken) {
            // Deliberately skip JSON. This is Java's internal object
            // representation, not the shared wire format the server expects.
            String raw = greeting.toString();
            System.out.println("BROKEN MODE: presentation layer removed");
            System.out.println("Sending raw Java representation: " + raw);
            wireMessage = raw + "\n";
        } else {
            // Presentation layer: application data -> agreed JSON wire format.
            String json = String.format("{\"type\": \"%s\", \"name\": \"%s\"}", greeting.type, greeting.name);
            System.out.println("NORMAL MODE: JSON presentation layer enabled");
            System.out.println("Sending JSON: " + json);
            wireMessage = json + "\n";
        }

        try (Socket socket = new Socket(host, port)) {
            OutputStream out = socket.getOutputStream();
            out.write(wireMessage.getBytes(StandardCharsets.UTF_8));
            out.flush();

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            String replyLine = reader.readLine();

            if (replyLine == null) {
                System.out.println("No reply from server.");
                return;
            }
            System.out.println("Raw server reply: " + replyLine);
        }
    }
}
