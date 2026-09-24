// Tiny TCP client showing why a shared presentation format is needed.
//
// Every message is: headers (Name: value lines), a blank line, then exactly
// Content-Length bytes of body. The Python server reads the Content-Type
// header to pick the decoder, so the format can change per request without
// restarting it. Rust's own Debug representation of a struct is none of the
// formats it understands and has no headers, so sending it "as is"
// demonstrates the same point as client.py's --remove-presentation flag,
// but from Rust this time. No external crates: builds fully offline.

use std::collections::HashMap;
use std::env;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::Duration;

#[derive(Debug)]
struct Greeting {
    msg_type: String,
    name: String,
}

fn json_string(value: &str) -> String {
    let mut out = String::from("\"");
    for c in value.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
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
            "{{\"type\": {}, \"name\": {}}}",
            json_string(&greeting.msg_type),
            json_string(&greeting.name)
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

    let wire_message: Vec<u8> = if broken {
        // Deliberately skip the headers and serialization. This is Rust's
        // internal Debug representation, not the shared wire format the
        // server expects.
        println!("BROKEN MODE: presentation layer removed");
        let raw = format!("{:?}", greeting);
        println!("Sending raw Rust representation: {}", raw);
        format!("{}\n", raw).into_bytes()
    } else {
        // Presentation layer: application data -> agreed wire format. The
        // header names the format and Content-Length counts BYTES (str::len
        // is the UTF-8 byte length).
        let body = encode_body(&format, &greeting).unwrap_or_else(|error| {
            eprintln!("{}", error);
            std::process::exit(1);
        });
        println!("NORMAL MODE: {} presentation layer enabled", format.to_uppercase());
        println!("Sending body: {}", body);
        format!("Content-Type: {}\nContent-Length: {}\n\n{}", format, body.len(), body).into_bytes()
    };

    let address = (host.as_str(), port)
        .to_socket_addrs()?
        .next()
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::InvalidInput, "cannot resolve host"))?;
    let mut stream = TcpStream::connect_timeout(&address, Duration::from_secs(10))?;
    stream.set_read_timeout(Some(Duration::from_secs(10)))?;
    stream.write_all(&wire_message)?;

    let mut reader = BufReader::new(stream);
    let mut headers: HashMap<String, String> = HashMap::new();
    loop {
        let mut line = String::new();
        let read = reader.read_line(&mut line)?;
        let line = line.trim_end_matches(['\r', '\n']);
        if line.is_empty() {
            if read == 0 && headers.is_empty() {
                println!("No reply from server.");
                return Ok(());
            }
            break;
        }
        if let Some((key, value)) = line.split_once(':') {
            headers.insert(key.trim().to_lowercase(), value.trim().to_string());
        }
    }

    let length: usize = match headers.get("content-length").and_then(|v| v.parse().ok()) {
        Some(length) => length,
        None => {
            println!("Reply has no valid Content-Length");
            return Ok(());
        }
    };
    let mut reply_body = vec![0u8; length];
    reader.read_exact(&mut reply_body)?;
    println!("Reply headers: {:?}", headers);
    println!("Reply body: {}", String::from_utf8_lossy(&reply_body));

    Ok(())
}
