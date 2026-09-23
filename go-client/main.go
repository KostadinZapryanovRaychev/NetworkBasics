// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) reads a Content-Type header line before the
// body, so the format can change per request without restarting the server.
// Go's default %+v struct dump is none of the formats it understands, and
// skips the header entirely, so sending it "as is" demonstrates the same
// point as client.py's --remove-presentation flag. No dependencies:
// standard library only.

package main

import (
	"bufio"
	"flag"
	"fmt"
	"net"
	"net/url"
)

type Greeting struct {
	Type string
	Name string
}

func encodeBody(format string, greeting Greeting) (string, error) {
	switch format {
	case "json":
		return fmt.Sprintf(`{"type": "%s", "name": "%s"}`, greeting.Type, greeting.Name), nil
	case "urlencoded":
		values := url.Values{}
		values.Set("type", greeting.Type)
		values.Set("name", greeting.Name)
		return values.Encode(), nil
	default:
		return "", fmt.Errorf("unsupported format: %s", format)
	}
}

func main() {
	host := flag.String("host", "127.0.0.1", "server host")
	port := flag.Int("port", 5001, "server port")
	name := flag.String("name", "Student", "greeting name")
	format := flag.String("format", "json", "presentation format: json or urlencoded")
	broken := flag.Bool("broken", false, "send Go's native struct dump instead of a header and body")
	flag.Parse()

	greeting := Greeting{Type: "greeting", Name: *name}

	var wireMessage string
	if *broken {
		// Deliberately skip both the header and serialization. This is Go's
		// internal struct representation, not the shared wire format the
		// server expects, and there is no Content-Type line either.
		raw := fmt.Sprintf("%+v", greeting)
		fmt.Println("BROKEN MODE: presentation layer removed")
		fmt.Println("Sending raw Go representation:", raw)
		wireMessage = raw + "\n"
	} else {
		// Presentation layer: application data -> agreed wire format, with
		// a Content-Type header so the server knows which one without
		// being told in advance.
		body, err := encodeBody(*format, greeting)
		if err != nil {
			fmt.Println(err)
			return
		}
		fmt.Println("NORMAL MODE:", *format, "presentation layer enabled")
		fmt.Println("Sending body:", body)
		wireMessage = "Content-Type: " + *format + "\n" + body + "\n"
	}

	address := fmt.Sprintf("%s:%d", *host, *port)
	conn, err := net.Dial("tcp", address)
	if err != nil {
		fmt.Println("Connection error:", err)
		return
	}
	defer conn.Close()

	_, err = conn.Write([]byte(wireMessage))
	if err != nil {
		fmt.Println("Write error:", err)
		return
	}

	reader := bufio.NewReader(conn)
	replyHeader, err := reader.ReadString('\n')
	if err != nil && replyHeader == "" {
		fmt.Println("No reply from server.")
		return
	}
	fmt.Println("Reply header:", replyHeader[:len(replyHeader)-1])

	replyBody, err := reader.ReadString('\n')
	if err == nil {
		replyBody = replyBody[:len(replyBody)-1]
	}
	fmt.Println("Reply body:", replyBody)
}
