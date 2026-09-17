// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) only understands the wire formats defined
// in protocol.py (JSON, XML, CSV, pickle). Rust's own Debug representation
// of a struct is none of those, so sending it "as is" demonstrates the same
// point as client.py's --broken flag and the C# client's --broken flag,
// but from Rust this time. No external crates: builds fully offline.

use std::env;
use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;

#[derive(Debug)]
struct Greeting {
    msg_type: String,
    name: String,
}

fn main() -> std::io::Result<()> {
    let mut host = "127.0.0.1".to_string();
    let mut port: u16 = 5001;
    let mut name = "Student".to_string();
    let mut broken = false;

    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--host" => {
                i += 1;
                host = args[i].clone();
            }
            "--port" => {
                i += 1;
                port = args[i].parse().expect("--port must be a number");
            }
            "--name" => {
                i += 1;
                name = args[i].clone();
            }
            "--broken" => {
                broken = true;
            }
            other => {
                eprintln!("Unknown argument: {}", other);
            }
        }
        i += 1;
    }

    let greeting = Greeting {
        msg_type: "greeting".to_string(),
        name: name.clone(),
    };

    let wire_message: String = if broken {
        // Deliberately skip JSON. This is Rust's internal Debug
        // representation, not the shared wire format the server expects.
        println!("BROKEN MODE: presentation layer removed");
        let raw = format!("{:?}", greeting);
        println!("Sending raw Rust representation: {}", raw);
        raw
    } else {
        // Presentation layer: application data -> agreed JSON wire format.
        let json = format!(
            "{{\"type\": \"{}\", \"name\": \"{}\"}}",
            greeting.msg_type, greeting.name
        );
        println!("NORMAL MODE: JSON presentation layer enabled");
        println!("Sending JSON: {}", json);
        json
    };

    let address = format!("{}:{}", host, port);
    let mut stream = TcpStream::connect(&address)?;
    stream.write_all(wire_message.as_bytes())?;
    stream.write_all(b"\n")?;

    let mut reader = BufReader::new(stream);
    let mut reply_line = String::new();
    reader.read_line(&mut reply_line)?;

    if reply_line.is_empty() {
        println!("No reply from server.");
        return Ok(());
    }

    println!("Raw server reply: {}", reply_line.trim_end());
    Ok(())
}
