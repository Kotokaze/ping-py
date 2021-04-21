import socket
import time
import random
import struct
import string
import select
from array import array

ICMP_ECHOREPLY = 0  # Echo reply
ICMP_ECHO = 8  # Echo request
DATA_LENGTH = 512  # The length of data
BUF_SIZE = 1024
TIMELIM = 3000  # milliseconds

class Ping:
	def __init__(self, dest, myId) -> None:
			self.dest = dest
			self.myId = myId
			self.packet: bytes = None
			self.length: int = DATA_LENGTH
			self.seqNum: int = 0
			self.checksum: int = 0
			self.timelim: int = TIMELIM
			self.count: int = 0

	def ping(self) -> None:
		"""
			ping を実行するメインプログラム
		"""
		try:
			self.dest = socket.gethostbyname(self.dest)
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			send_time = self._send(sock)
			recv_time, recv_data = self._recv(sock)
		except OSError as e:
			print(e)
		finally:
			sock.close()

		if recv_data:
			elapse = (recv_time - send_time) * 1000
			print("{} bytes from {}: icmp_seq={} ttl={} time={:.3f} ms".format(int(recv_data[0]/8), recv_data[1], recv_data[2], recv_data[3], elapse))

	def _send(self, sock) -> float:
		"""
			ICMP エコー要求を飛ばす関数
			Args:
				sock socket
			Returns:
				float 送信時刻
		"""
		# Generate Temp Packet
		checksum = 0
		header: bytes = struct.pack("!BBHHH", ICMP_ECHO, 0, checksum, self.myId, self.seqNum)
		data: bytes = self._random().encode('utf-8')
		packet: bytes = header + data

		self.checksum = self._checksum(packet)

		# Generate Packet
		header = struct.pack("!BBHHH", ICMP_ECHO, 0, self.checksum, self.myId, self.seqNum)
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
		"""
			ICMP リプライを受信する
			Return:
				tuple [受信時刻, 受信データ]
		"""
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
			packet, src = sock.recvfrom(BUF_SIZE)

			raw = packet[20:28]
			icmp_header = self._icmp_header(raw)

			if (icmp_header["packetId"] == self.myId) and (hex(self._checksum(raw[20:22] + raw[25:28]))):
				raw = packet[:20]
				ip_header = self._ip_header(raw)
				packet_size = len(packet) - 28
				self.count += 1
				return recv_time, (packet_size, src[0], icmp_header['seq'], ip_header['ttl'])

	def _random(self) -> str:
		"""
			ランダムな文字列を生成する関数
			Return:
				str ランダム文字列
		"""
		return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(self.length))

	def _checksum(self, data) -> int:
		# Exception handling for odd numbers
		if (len(data)%2 != 0):
			data += '\x00'

		arr = array("H", data)
		val = sum(arr)

		val &= 0xffffffff
		val = (val >> 16) + (val & 0xffff)
		val = (val >> 16) + (val & 0xffff)
		ans = ~val & 0xffff
		ans = socket.htons(ans)
		return ans

	def _icmp_header(self, raw) -> dict:
		"""
			ICMP ヘッダの Raw データを変換
		"""
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
		"""
			IP ヘッダの Raw データを変換
		"""
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
		return data

	def _statistics(self) -> None:
		print(f"\n\n--- {self.dest} ping statistics ---")
		print(f"{self.seqNum} packets transmitted, {self.count} packets received, {(100 * (self.seqNum - self.count))/self.seqNum}% packet loss")

	def __str__(self) -> str:
		return f"PING {self.dest}: {int(self.length / 8)} data bytes"
