import struct


def recv_all(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise OSError("Connection closed before receiving all data")
        data += chunk
    return data


def recv_message(sock):
    header = recv_all(sock, 4)
    length = struct.unpack('!I', header)[0]
    return recv_all(sock, length).decode('utf-8')


def send_message(sock, message):
    payload = message.encode('utf-8')
    header = struct.pack('!I', len(payload))
    send_all(sock, header + payload)


def send_all(sock, data):
    total = 0
    while total < len(data):
        sent = sock.send(data[total:])
        if sent == 0:
            raise OSError("Connection closed before sending all data")
        total += sent
