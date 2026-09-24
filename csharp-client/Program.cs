// Tiny TCP client showing why a shared presentation format is needed.
//
// Every message is: headers (Name: value lines), a blank line, then exactly
// Content-Length bytes of body. The Python server reads the Content-Type
// header to pick the decoder, so the format can change per request without
// restarting it. A .NET object's own ToString() representation is none of
// the formats it understands and has no headers, so sending it "as is"
// demonstrates the same point as client.py's --remove-presentation flag,
// but across languages this time.

using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

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
    // Deliberately skip the headers and serialization. This is C#'s internal
    // representation (record ToString()), not the shared wire format the
    // server expects.
    wireMessage = Encoding.UTF8.GetBytes(greeting.ToString() + "\n");
    Console.WriteLine("BROKEN MODE: presentation layer removed");
    Console.WriteLine("Sending raw .NET representation: " + greeting);
}
else
{
    // Presentation layer: application data -> agreed wire format. The header
    // names the format and Content-Length counts BYTES, not characters.
    string body = format switch
    {
        "json" => JsonSerializer.Serialize(new { type = greeting.Type, name = greeting.Name }),
        "urlencoded" => $"type={WebUtility.UrlEncode(greeting.Type)}&name={WebUtility.UrlEncode(greeting.Name)}",
        _ => throw new ArgumentException("Unsupported format: " + format),
    };
    byte[] bodyBytes = Encoding.UTF8.GetBytes(body);
    byte[] head = Encoding.UTF8.GetBytes($"Content-Type: {format}\nContent-Length: {bodyBytes.Length}\n\n");
    wireMessage = head.Concat(bodyBytes).ToArray();
    Console.WriteLine($"NORMAL MODE: {format.ToUpperInvariant()} presentation layer enabled");
    Console.WriteLine("Sending body: " + body);
}

using var client = new TcpClient { ReceiveTimeout = 10000, SendTimeout = 10000 };
await client.ConnectAsync(host, port).WaitAsync(TimeSpan.FromSeconds(10));
using NetworkStream network = client.GetStream();
await network.WriteAsync(wireMessage);

using var stream = new BufferedStream(network);

string? ReadLine()
{
    var line = new List<byte>();
    int b;
    while ((b = stream.ReadByte()) != -1)
    {
        if (b == '\n')
        {
            return Encoding.UTF8.GetString(line.ToArray());
        }
        line.Add((byte)b);
    }
    return line.Count == 0 ? null : Encoding.UTF8.GetString(line.ToArray());
}

var headers = new Dictionary<string, string>();
string? headerLine;
while ((headerLine = ReadLine()) is not null && headerLine.Trim().Length > 0)
{
    int colon = headerLine.IndexOf(':');
    if (colon > 0)
    {
        headers[headerLine[..colon].Trim().ToLowerInvariant()] = headerLine[(colon + 1)..].Trim();
    }
}

if (headers.Count == 0)
{
    Console.WriteLine("No reply from server.");
    return;
}
if (!headers.TryGetValue("content-length", out string? lengthText) || !int.TryParse(lengthText, out int length))
{
    Console.WriteLine("Reply has no valid Content-Length");
    return;
}

var replyBody = new byte[length];
int read = 0;
while (read < length)
{
    int n = stream.Read(replyBody, read, length - read);
    if (n == 0)
    {
        Console.WriteLine("Reply body was cut short");
        return;
    }
    read += n;
}

Console.WriteLine("Reply headers: " + string.Join(", ", headers.Select(h => $"{h.Key}={h.Value}")));
Console.WriteLine("Reply body: " + Encoding.UTF8.GetString(replyBody));

record Greeting(string Type, string Name);
