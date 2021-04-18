#! /usr/bin/env python3
import os
import socket
import time
import random
import struct
import string
import select
from array import array
from _thread import get_ident

ICMP_ECHOREPLY = 0  # Echo reply
ICMP_ECHO = 8  # Echo request
DATA_LENGTH = 32  # The length of data
TIMELIM = 1000  # milliseconds


class Ping:
	def __init__(self) -> None:
			self.dest = None
			self.myId = None
			self.packet: bytes = None
			self.length: int = DATA_LENGTH
			self.seqNum: int = 0
			self.timelim: int = TIMELIM

	def ping(self) -> None:
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		except OSError as e:
			print(e)
			exit(-1)

		send_time = self._send(sock)
		recv_time, recv_data = self._recv(sock)
		sock.close()

		if recv_data:
			elapse = (recv_time - send_time) * 1000
			print("{} bytes from {}: time={} ms".format(recv_data[0], recv_data[1], elapse))
			# {} bytes from {}: icmp_seq={} ttl={} time={} ms

	def _send(self, sock) -> float:
		# Generate Temp Packet
		checksum: int = 0
		header: bytes = struct.pack("!BBHHH", ICMP_ECHO, 0, checksum, self.myId, self.seqNum)
		data: bytes = self._random().encode('utf-8')
		packet: bytes = header + data

		checksum = self._checksum(packet)

		# Generate Packet
		header = struct.pack("!BBHHH", ICMP_ECHO, 0, checksum, self.myId, self.seqNum)
		self.packet = header + data

		try:
			send_time: float = time.time()
			sock.sendto(self.packet, (self.dest, 1))
			# print("sending...")
		except OSError as e:
			print("Fail to Send\n%s" %e)
			exit(-1)

		return send_time

	def _recv(self, sock) -> tuple:
		timeleft: float = self.timelim / 1000
		start = time.time()

		while True:
			ready = select.select([sock], [], [], timeleft)
			elapse = time.time() - start
			timeleft -= elapse

			if not ready[0]:
				print("Request timeout for icmp_seq ", str(self.seqNum))
				return None, (None)

			recv_time = time.time()
			packet, src = sock.recvfrom(self.length)

			raw = packet[20:28]
			icmp_header = self._icmp_header(raw)

			if icmp_header["packetId"] == self.myId:
				raw = packet[:20]
				ip_header = self._ip_header(raw)
				packet_size = len(packet) - 28
				return recv_time, (packet_size, src[0], ip_header, icmp_header)

	def _random(self) -> str:
		return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(self.length))

	def _checksum(self, data) -> int:
		# Exception handling for odd numbers
		if (len(data)%2 != 0):
			data += '\x00'

		arr = array("H", data)
		val = sum(arr)

		val &= 0xffffffff
		val = (val >> 16) + (val & 0xffff)
		val += (val >> 16)
		ans = ~val & 0xffff
		ans = socket.htons(ans)
		return ans

	def _icmp_header(self, raw) -> dict:
		icmp_header = struct.unpack('!bbHHh', raw)
		data = {
			'type': icmp_header[0],
			'code': icmp_header[1],
			'checksum': icmp_header[2],
			'packetId': icmp_header[3],
			'seq': icmp_header[4]
		}
		return data

	def _ip_header(self, raw) -> dict:
		ip_header = struct.unpack('!BBHHHBBHII', raw)
		data = {
			'version': ip_header[0],
			'type': ip_header[1],
			'length': ip_header[2],
			'id': ip_header[3],
			'flags': ip_header[4],
			'ttl': ip_header[5],
			'protocol': ip_header[6],
			'checksum': ip_header[7],
			'src_ip': ip_header[8],
			'dest_ip': ip_header[9]
		}
		return ip_header

	def __str__(self) -> str:
		strings = "PING {}: {} bytes of data".format(self.dest, self.length)
		return strings


def main() -> None:
	ping = Ping()
	ping.dest = '127.0.0.1'
	ping.myId = (os.getpid() ^ get_ident()) & 0xFFFF
	# ping.ping()

	try:
		while True:
			ping.ping()
			ping.seqNum += 1
	except KeyboardInterrupt:
		exit(0)

if __name__ == '__main__':
	main()
