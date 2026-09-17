// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) only understands the wire formats defined
// in protocol.py (JSON, XML, CSV, pickle). Go's default %+v struct dump is
// none of those - it looks close to JSON but still fails to parse as it,
// which makes it a good "near miss" example alongside the other clients'
// --broken flag. No dependencies: standard library only.

package main

import (
	"bufio"
	"flag"
	"fmt"
	"net"
)

type Greeting struct {
	Type string
	Name string
}

func main() {
	host := flag.String("host", "127.0.0.1", "server host")
	port := flag.Int("port", 5001, "server port")
	name := flag.String("name", "Student", "greeting name")
	broken := flag.Bool("broken", false, "send Go's native struct dump instead of JSON")
	flag.Parse()

	greeting := Greeting{Type: "greeting", Name: *name}

	var wireMessage string
	if *broken {
		// Deliberately skip JSON. This is Go's internal struct
		// representation, not the shared wire format the server expects.
		raw := fmt.Sprintf("%+v", greeting)
		fmt.Println("BROKEN MODE: presentation layer removed")
		fmt.Println("Sending raw Go representation:", raw)
		wireMessage = raw + "\n"
	} else {
		// Presentation layer: application data -> agreed JSON wire format.
		json := fmt.Sprintf(`{"type": "%s", "name": "%s"}`, greeting.Type, greeting.Name)
		fmt.Println("NORMAL MODE: JSON presentation layer enabled")
		fmt.Println("Sending JSON:", json)
		wireMessage = json + "\n"
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
	replyLine, err := reader.ReadString('\n')
	if err != nil && replyLine == "" {
		fmt.Println("No reply from server.")
		return
	}
	fmt.Println("Raw server reply:", replyLine[:len(replyLine)-1])
}
