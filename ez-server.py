#! /usr/bin/env python
# coding=utf-8
# author: Rand01ph

import socket
import sys
import struct

# Create a TCP/IP socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to the port
server_address = ('localhost', 10000)
print('starting up on {} port {}'.format(*server_address))
server_sock.bind(server_address)
# Listen for incoming connections
server_sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = server_sock.accept()
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
    ver, cmd, rsv, atype = connection.recv(1),connection.recv(1),connection.recv(1),connection.recv(1)
    print("the protocal ver {}, cmd {}, rsv {}, atype {}".format(ver, cmd, rsv, atype))

    if ord(cmd) is not 1:
        connection.close()
        break

    if ord(atype) == 1:
        remote_addr = socket.inet_ntoa(connection.recv(4))
        remote_port = struct.unpack("!H", connection.recv(2))[0]
    elif ord(atype) == 3:
        addr_len = ord(connection.recv(1))
        remote_addr = connection.recv(addr_len)
        remote_port = struct.unpack("!H", connection.recv(2))[0]
    else:
        # 不支持的地址类型
        reply = b"\x05\x08\x00\x01" + inet_aton("0.0.0.0") + struct.pack("!H", 9998)
        connection.send(reply)
        connection.close()
        break

    print("remote target ----------- {}:{}".format(remote_addr, remote_port))

    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_address = (remote_addr, remote_port)
    remote_sock.connect(remote_address)
