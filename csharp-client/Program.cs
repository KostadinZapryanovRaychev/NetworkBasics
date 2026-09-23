// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) reads a Content-Type header line before the
// body, so the format can change per request without restarting the server.
// A .NET object's own ToString() representation is none of the formats it
// understands, and skips the header entirely, so sending it "as is"
// demonstrates the same point as client.py's --remove-presentation flag,
// but across languages this time.

using System.Net;
using System.Net.Sockets;
using System.Text;

string host = "127.0.0.1";
int port = 5001;
string name = "Student";
string format = "json";
bool broken = false;

for (int i = 0; i < args.Length; i++)
{
    switch (args[i])
    {
        case "--host":
            host = args[++i];
            break;
        case "--port":
            port = int.Parse(args[++i]);
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

var greeting = new Greeting("greeting", name);

byte[] wireMessage;
if (broken)
{
    // Deliberately skip both the header and serialization. This is C#'s
    // internal representation (record ToString()), not the shared wire
    // format the server expects, and there is no Content-Type line either.
    string raw = greeting.ToString() + "\n";
    wireMessage = Encoding.UTF8.GetBytes(raw);
    Console.WriteLine("BROKEN MODE: presentation layer removed");
    Console.WriteLine("Sending raw .NET representation: " + greeting);
}
else
{
    // Presentation layer: application data -> agreed wire format, with a
    // Content-Type header so the server knows which one without being
    // told in advance.
    string body = format switch
    {
        "json" => $"{{\"type\": \"{greeting.Type}\", \"name\": \"{greeting.Name}\"}}",
        "urlencoded" => $"type={WebUtility.UrlEncode(greeting.Type)}&name={WebUtility.UrlEncode(greeting.Name)}",
        _ => throw new ArgumentException("Unsupported format: " + format),
    };
    string request = $"Content-Type: {format}\n{body}\n";
    wireMessage = Encoding.UTF8.GetBytes(request);
    Console.WriteLine($"NORMAL MODE: {format.ToUpperInvariant()} presentation layer enabled");
    Console.WriteLine("Sending body: " + body);
}

using var client = new TcpClient();
await client.ConnectAsync(host, port);
using NetworkStream stream = client.GetStream();
await stream.WriteAsync(wireMessage);

using var reader = new StreamReader(stream, Encoding.UTF8);
string? replyHeader = await reader.ReadLineAsync();
string? replyBody = await reader.ReadLineAsync();

if (replyHeader is null)
{
    Console.WriteLine("No reply from server.");
    return;
}

Console.WriteLine("Reply header: " + replyHeader);
Console.WriteLine("Reply body: " + replyBody);

record Greeting(string Type, string Name);
