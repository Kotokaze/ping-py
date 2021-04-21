#! /usr/bin/env python3
import os
from ping import Ping
from _thread import get_ident

def main() -> None:
	dest = input("Enter the target: ")
	myId = (os.getpid() ^ get_ident()) & 0xFFFF
	ping = Ping(dest, myId)
	print(str(ping))

	try:
		while True:
			ping.ping()
			ping.seqNum += 1
	except KeyboardInterrupt:
		ping._statistics()
		exit(0)

if __name__ == '__main__':
	main()
