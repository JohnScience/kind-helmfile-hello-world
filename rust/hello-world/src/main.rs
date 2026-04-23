use std::{
    io::{Read, Write},
    net::{Shutdown, TcpListener},
};

fn main() {
    let addr = "0.0.0.0:8080";
    let listener = TcpListener::bind(addr).expect("failed to bind to address");
    println!("Hello World server listening on {addr}");

    for stream in listener.incoming() {
        let mut stream = match stream {
            Ok(s) => s,
            Err(e) => {
                eprintln!("connection error: {e}");
                continue;
            }
        };

        let mut buffer = [0u8; 4096];
        let bytes_read = match stream.read(&mut buffer) {
            Ok(0) => {
                eprintln!("debug: 0-byte read (peer closed before sending request)");
                continue;
            }
            Ok(n) => n,
            Err(e) => {
                eprintln!("read error: {e}");
                continue;
            }
        };

        let request = String::from_utf8_lossy(&buffer[..bytes_read]);
        let first_line = request.lines().next().unwrap_or("");
        let path = first_line.split_whitespace().nth(1).unwrap_or("/");

        println!("request: {first_line}");

        let (status, body) = match path {
            "/health" => ("200 OK", "ok"),
            "/" => ("200 OK", "Hello, World!"),
            _ => ("404 Not Found", "not found"),
        };

        let response = format!(
            "HTTP/1.1 {status}\r\nContent-Type: text/plain\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
            body.len()
        );

        if let Err(e) = stream.write_all(response.as_bytes()) {
            eprintln!("write error: {e}");
            continue;
        }
        println!("response: {status}");
        let _ = stream.shutdown(Shutdown::Write);
    }
}
