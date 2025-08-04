#!/usr/bin/env python
# mypy: ignore-errors

from struct import unpack

from six import BytesIO, b

from . import dumps, loads


def _bintoint(data):
    return unpack("<i", data)[0]


def sendobj(self, obj):
    """
        Atomically send a BSON message.
    """
    data = dumps(obj)
    self.sendall(data)


def recvobj(self):
    """
        Atomic read of a BSON message.

        This function either returns a dict, None, or raises a socket error.

        If the return value is None, it means the socket is closed by the other side.
    """
    sock_buf = self.recvbytes(4)
    if sock_buf is None:
        return None

    message_length = _bintoint(sock_buf.getvalue())
    sock_buf = self.recvbytes(message_length - 4, sock_buf)
    if sock_buf is None:
        return None

    retval = loads(sock_buf.getvalue())
    return retval


def recvbytes(self, bytes_needed, sock_buf = None):
    """
        Atomic read of bytes_needed bytes.

        This function either returns exactly the nmber of bytes requested in a
        StringIO buffer, None, or raises a socket error.

        If the return value is None, it means the socket is closed by the other side.
    """
    if sock_buf is None:
        sock_buf = BytesIO()
    bytes_count = 0
    while bytes_count < bytes_needed:
        chunk = self.recv(min(bytes_needed - bytes_count, 32768))
        part_count = len(chunk)

        if type(chunk) == str:
            chunk = b(chunk)

        if part_count < 1:
            return None

        bytes_count += part_count
        sock_buf.write(chunk)

    return sock_buf
