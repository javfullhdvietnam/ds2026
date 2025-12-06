import os
import socket
import struct
import sys
from contextlib import closing

BUFFER_SIZE = 65536

DEFAULT_HOST = "0.0.0.0"  # listen on all interfaces by default
DEFAULT_PORT = 9000


def recvall(conn, n):
    data = bytearray()
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

def recv_file(conn):
    name_len_bytes = recvall(conn, 2)
    if not name_len_bytes:
        raise RuntimeError("Failed to read filename length")
    name_len = struct.unpack("!H", name_len_bytes)[0]
    if name_len == 0 or name_len > 255:
        raise RuntimeError("Invalid filename length")

    name_bytes = recvall(conn, name_len)
    if not name_bytes:
        raise RuntimeError("Failed to read filename")
    filename = name_bytes.decode("utf-8", errors="replace")

    size_bytes = recvall(conn, 8)
    if not size_bytes:
        raise RuntimeError("Failed to read file size")
    remaining = struct.unpack("!Q", size_bytes)[0]

    print(f"Receiving {filename} ({remaining} bytes)...")
    with open(filename, "wb") as outf:
        while remaining:
            chunk = conn.recv(BUFFER_SIZE if remaining > BUFFER_SIZE else remaining)
            if not chunk:
                raise RuntimeError("Connection closed early")
            outf.write(chunk)
            remaining -= len(chunk)
    print("Saved to", filename)


def main():
    # Defaults make it runnable without arguments; args still override.
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    if len(sys.argv) == 1:
        pass  # use defaults
    elif len(sys.argv) == 2:
        port = int(sys.argv[1])
    elif len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        print(f"Usage: python {sys.argv[0]} [host] [port]")
        print("Examples:")
        print(f"  python {sys.argv[0]}            # uses {DEFAULT_HOST}:{DEFAULT_PORT}")
        print(f"  python {sys.argv[0]} 9000       # host default, port override")
        print(f"  python {sys.argv[0]} 127.0.0.1 9000")
        return 1

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(1)
        listen_host = host if host else "0.0.0.0"
        print(f"Listening on {listen_host}:{port} ...")
        conn, addr = srv.accept()
        with closing(conn):
            print("Connection from", addr)
            recv_file(conn)
    return 0

if __name__ == "__main__":
    sys.exit(main())
