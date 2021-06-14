#!/usr/bin/env python3

import serial  # pip3 install pyserial
import argparse
import logging as log
import socket
import signal


def main():
    parser = argparse.ArgumentParser(
            description='A simple program for redirecting ZPL print jobs from'
                        ' a virtual COM port to a networked Zebra printer'
                        ' over TCP.')

    parser.add_argument('--port', '-p', type=int, default=9100,
                        help='TCP port the printer listens on'
                             ' (default: %(default)d)')

    parser.add_argument('COM',
                        help='the virtual serial port created by com0com')

    parser.add_argument('host',
                        help="the printer's IP address")

    global args
    args = parser.parse_args()

    log.basicConfig(level=log.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s')

    ser = serial.Serial(args.COM)
    log.info(f"Listening on {ser.name}")
    received_data = bytearray("aaa", 'ascii')
    sending = False
    sock = None

    signal.signal(signal.SIGINT, signal.default_int_handler)

    try:
        while True:
            c = ser.read(1)

            if sending:
                sock.send(c)  # TODO care about the return value ??

            for i in range(2):
                received_data[i] = received_data[i+1]
            received_data[2] = ord(c)

            if sending and received_data == bytearray("^XZ", 'ascii'):
                # already sent ^XZ
                log.info("Closing TCP connection")
                sock.close()
                sock = None
                sending = False

            if not sending and received_data == bytearray("^XA", 'ascii'):
                sending = True
                log.info("Starting TCP connection")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((args.host, args.port))
                sock.send(b"^XA")
    except KeyboardInterrupt:
        # TODO ctrl+c keeps waiting for a character on the COM port?!
        # Windows only??
        log.info("Keyboard Interrupt")
        ser.close()
        if sock is not None:
            sock.close()


if __name__ == '__main__':
    main()
