// Tiny TCP client showing why a shared presentation format is needed.
//
// The Python server (server.py) reads a Content-Type header line before the
// body, so the format can change per request without restarting the server.
// Rust's own Debug representation of a struct is none of the formats it
// understands, and skips the header entirely, so sending it "as is"
// demonstrates the same point as client.py's --remove-presentation flag,
// but from Rust this time. No external crates: builds fully offline.

use std::env;
use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;

#[derive(Debug)]
struct Greeting {
    msg_type: String,
    name: String,
}

fn form_urlencode(value: &str) -> String {
    let mut out = String::new();
    for byte in value.bytes() {
        match byte {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                out.push(byte as char);
            }
            b' ' => out.push('+'),
            _ => out.push_str(&format!("%{:02X}", byte)),
        }
    }
    out
}

fn encode_body(format: &str, greeting: &Greeting) -> Result<String, String> {
    match format {
        "json" => Ok(format!(
            "{{\"type\": \"{}\", \"name\": \"{}\"}}",
            greeting.msg_type, greeting.name
        )),
        "urlencoded" => Ok(format!(
            "type={}&name={}",
            form_urlencode(&greeting.msg_type),
            form_urlencode(&greeting.name)
        )),
        other => Err(format!("Unsupported format: {}", other)),
    }
}

fn main() -> std::io::Result<()> {
    let mut host = "127.0.0.1".to_string();
    let mut port: u16 = 5001;
    let mut name = "Student".to_string();
    let mut format = "json".to_string();
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
            "--format" => {
                i += 1;
                format = args[i].clone();
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
        // Deliberately skip both the header and serialization. This is
        // Rust's internal Debug representation, not the shared wire format
        // the server expects, and there is no Content-Type line either.
        println!("BROKEN MODE: presentation layer removed");
        let raw = format!("{:?}", greeting);
        println!("Sending raw Rust representation: {}", raw);
        raw
    } else {
        // Presentation layer: application data -> agreed wire format, with
        // a Content-Type header so the server knows which one without
        // being told in advance.
        let body = encode_body(&format, &greeting).expect("encode_body failed");
        println!("NORMAL MODE: {} presentation layer enabled", format.to_uppercase());
        println!("Sending body: {}", body);
        format!("Content-Type: {}\n{}", format, body)
    };

    let address = format!("{}:{}", host, port);
    let mut stream = TcpStream::connect(&address)?;
    stream.write_all(wire_message.as_bytes())?;
    stream.write_all(b"\n")?;

    let mut reader = BufReader::new(stream);
    let mut reply_header = String::new();
    reader.read_line(&mut reply_header)?;
    println!("Reply header: {}", reply_header.trim_end());

    let mut reply_body = String::new();
    reader.read_line(&mut reply_body)?;
    println!("Reply body: {}", reply_body.trim_end());

    Ok(())
}
