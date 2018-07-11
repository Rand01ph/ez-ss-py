#! /usr/bin/env python
# coding=utf-8
# author: Rand01ph

import socket
import sys

# Create a TCP/IP socket
local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
local_address = ('localhost', 8989)
server_address = ('localhost', 10000)

server_sock.connect(server_address)
local_sock.bind(local_address)
# Listen for incoming connections
local_sock.listen(1)

print('listen to {} port {}'.format(*local_address))
print('connecting to {} port {}'.format(*server_address))

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = local_sock.accept()
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(16)
            print('received {!r}'.format(data))
            if data:
                print('sending data to the server')
                server_sock.sendall(data)
            else:
                print('no data from', client_address)
                break
    finally:
        # Clean up the connection
        connection.close()
