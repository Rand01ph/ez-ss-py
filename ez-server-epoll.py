#! /usr/bin/env python
# coding=utf-8
# author: Rand01ph

import socket
import sys
import struct
import select
import threading

# curl -vv -x socks5h://127.0.0.1:10000 www.baidu.com

def handle_tcp(client, remote):
    try:
        print("handle_tcp")
        fd_list = [client, remote]
        while True:
            client_data = client.recv(1024 * 100)
            if len(client_data) > 0:
                print("client_data is {}".format(client_data))
                remote.sendall(client_data)

            remote_data = []
            while True:
                print("begin to recv from remote")
                chunk = remote.recv(1024 * 100)
                print("chunk is {}".format(chunk))
                if len(chunk) <= 0:
                    break
                else:
                    remote_data.append(chunk)
                print("remote_data is {}".format(remote_data))
            print("final remote_data is {}".format(remote_data))
            if remote_data:
                remote_data = b''.join(remote_data)
                client.sendall(remote_data)
                break
    except KeyboardInterrupt:
        client.close()
        remote.close()

def handle_connection(connection, client_address):
    print('connection from', client_address)

    # step1 begin to analyse socks5 protocol
    """
                +----+----------+----------+
                |VER | NMETHODS | METHODS  |
                +----+----------+----------+
                | 1  |    1     | 1 to 255 |
                +----+----------+----------+
    """
    ver, nmethods = connection.recv(1), connection.recv(1)
    methods = connection.recv(ord(nmethods))
    print("the protocal ver nmethods methods is {} {}".format(ver, nmethods, methods))
    connection.send(b'\x05\x00')

    """
        +----+-----+-------+------+----------+----------+
        |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
        +----+-----+-------+------+----------+----------+
        | 1  |  1  | X'00' |  1   | Variable |    2     |
        +----+-----+-------+------+----------+----------+
    """
    ver, cmd, rsv, atype = connection.recv(1), connection.recv(1), connection.recv(1), connection.recv(1)
    print("the protocal ver {}, cmd {}, rsv {}, atype {}".format(ver, cmd, rsv, atype))

    if ord(cmd) is not 1:
        connection.close()
        return

    if ord(atype) == 1:
        remote_addr = socket.inet_ntoa(connection.recv(4))
        remote_port = struct.unpack("!H", connection.recv(2))[0]
    elif ord(atype) == 3:
        addr_len = ord(connection.recv(1))
        remote_host = connection.recv(addr_len)
        print("remote_host is {0}".format(remote_host))
        remote_addr = socket.gethostbyname(remote_host)
        remote_port = struct.unpack("!H", connection.recv(2))[0]
    else:
        # 不支持的地址类型
        reply = b"\x05\x08\x00\x01" + socket.inet_aton("0.0.0.0") + struct.pack("!H", 9998)
        connection.send(reply)
        connection.close()
        return

    print("remote target ----------- {}:{}".format(remote_addr, remote_port))

    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_address = (remote_addr, remote_port)
    remote_sock.connect(remote_address)

    reply = b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + struct.pack("!H", 9998)
    connection.send(reply)

    handle_tcp(connection, remote_sock)



def main():
    # Create a TCP/IP socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the port
    server_address = ('localhost', 10000)
    print('starting up on {} port {}'.format(*server_address))
    server_sock.bind(server_address)
    # Listen for incoming connections
    server_sock.listen(1)

    try:
        while True:
            # Wait for a connection
            print('waiting for a connection')
            connection, client_address = server_sock.accept()
            t = threading.Thread(target=handle_connection, args=(connection, client_address))
            t.start()
    except socket.error as e:
        print(e)
    except KeyboardInterrupt:
        server_sock.close()

