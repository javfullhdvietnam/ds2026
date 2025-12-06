import os
import socket
import struct
import sys

BUFFER_SIZE = 65536


def send_file(host, port, path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    filename = os.path.basename(path)
    name_bytes = filename.encode("utf-8")
    if len(name_bytes) == 0 or len(name_bytes) > 255:
        raise ValueError("Filename must be 1-255 bytes after UTF-8 encoding")

    size = os.path.getsize(path)
    header = struct.pack("!H", len(name_bytes)) + name_bytes + struct.pack("!Q", size)

    with socket.create_connection((host, port)) as sock:
        sock.sendall(header)
        with open(path, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)

    print(f"Sent {path} to {host}:{port} ({size} bytes)")


def main():
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} <host> <port> <file>")
        return 1
    host = sys.argv[1]
    port = int(sys.argv[2])
    path = sys.argv[3]

    send_file(host, port, path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
