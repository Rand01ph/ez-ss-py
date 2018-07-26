#! /usr/bin/env python
# coding=utf-8
# author: Rand01ph

import socket
import sys
import struct
import select
import threading

# curl -vv -x socks5h://127.0.0.1:10000 www.baidu.com

epoll = select.epoll()


def handle_tcp(client, remote):
    """

    :param client:
    :type client: socket.socket
    :param remote:
    :type remote: socket.socket
    :return:
    """
    epoll.register(client.fileno(), select.EPOLLIN)
    epoll.register(remote.fileno(), select.EPOLLIN)
    client.setblocking(0)
    client.settimeout(10)
    remote.setblocking(0)
    remote.settimeout(10)
    try:
        while True:
            r_events = epoll.poll(1)
            for fileno, event in r_events:
                if fileno == client.fileno():
                    print("data from client")
                    client_data = client.recv(1024 * 100)
                    if len(client_data) > 0:
                        print("client_data is {}".format(client_data))
                        remote.sendall(client_data)
                    else:
                        return
                elif fileno == remote.fileno():
                    print("data from remote")
                    remote_data = remote.recv(1024 * 100)
                    if len(remote_data) > 0:
                        print("remote_data is {}".format(remote_data))
                        client.sendall(remote_data)
                    else:
                        return
    except Exception as e:
        raise e
    finally:
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
    server_sock.listen(1024)

    try:
        while True:
            # Wait for a connection
            print('waiting for a connection')
            connection, client_address = server_sock.accept()
#            handle_connection(connection, client_address)
            t = threading.Thread(target=handle_connection, args=(connection, client_address))
            t.start()
    except socket.error as e:
        print(e)
    finally:
        server_sock.close()


if __name__ == '__main__':
    main()
