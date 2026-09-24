// Tiny TCP client showing why a shared presentation format is needed.
//
// Every message is: headers (Name: value lines), a blank line, then exactly
// Content-Length bytes of body. The Python server reads the Content-Type
// header to pick the decoder, so the format can change per request without
// restarting it. Go's default %+v struct dump is none of the formats it
// understands and has no headers, so sending it "as is" demonstrates the
// same point as client.py's --remove-presentation flag. No dependencies:
// standard library only.

package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net"
	"net/url"
	"strconv"
	"strings"
	"time"
)

type Greeting struct {
	Type string `json:"type"`
	Name string `json:"name"`
}

func encodeBody(format string, greeting Greeting) (string, error) {
	switch format {
	case "json":
		data, err := json.Marshal(greeting)
		return string(data), err
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
	broken := flag.Bool("broken", false, "send Go's native struct dump instead of headers and a body")
	flag.Parse()

	greeting := Greeting{Type: "greeting", Name: *name}

	var wireMessage string
	if *broken {
		// Deliberately skip the headers and serialization. This is Go's
		// internal struct representation, not the shared wire format the
		// server expects.
		raw := fmt.Sprintf("%+v", greeting)
		fmt.Println("BROKEN MODE: presentation layer removed")
		fmt.Println("Sending raw Go representation:", raw)
		wireMessage = raw + "\n"
	} else {
		// Presentation layer: application data -> agreed wire format. The
		// header names the format and Content-Length counts BYTES (len of
		// a Go string is its byte length).
		body, err := encodeBody(*format, greeting)
		if err != nil {
			fmt.Println(err)
			return
		}
		fmt.Println("NORMAL MODE:", strings.ToUpper(*format), "presentation layer enabled")
		fmt.Println("Sending body:", body)
		wireMessage = fmt.Sprintf("Content-Type: %s\nContent-Length: %d\n\n%s", *format, len(body), body)
	}

	address := net.JoinHostPort(*host, strconv.Itoa(*port))
	conn, err := net.DialTimeout("tcp", address, 10*time.Second)
	if err != nil {
		fmt.Println("Connection error:", err)
		return
	}
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(10 * time.Second))

	if _, err = conn.Write([]byte(wireMessage)); err != nil {
		fmt.Println("Write error:", err)
		return
	}

	reader := bufio.NewReader(conn)
	headers := map[string]string{}
	for {
		line, err := reader.ReadString('\n')
		line = strings.TrimRight(line, "\r\n")
		if line == "" {
			if err != nil && len(headers) == 0 {
				fmt.Println("No reply from server.")
				return
			}
			break
		}
		if name, value, ok := strings.Cut(line, ":"); ok {
			headers[strings.ToLower(strings.TrimSpace(name))] = strings.TrimSpace(value)
		}
	}

	length, err := strconv.Atoi(headers["content-length"])
	if err != nil {
		fmt.Println("Reply has no valid Content-Length")
		return
	}
	replyBody := make([]byte, length)
	if _, err := io.ReadFull(reader, replyBody); err != nil {
		fmt.Println("Reply body was cut short:", err)
		return
	}
	fmt.Println("Reply headers:", headers)
	fmt.Println("Reply body:", string(replyBody))
}
