#! /usr/bin/env python3
import os
from ping import Ping
from _thread import get_ident

def main() -> None:
	ping = Ping()
	ping.dest = '127.0.0.1'  # 宛先
	ping.myId = (os.getpid() ^ get_ident()) & 0xFFFF

	try:
		while True:
			ping.ping()
			ping.seqNum += 1
	except KeyboardInterrupt:
		exit(0)

if __name__ == '__main__':
	main()
