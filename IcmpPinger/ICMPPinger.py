#!/usr/bin/python3
from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8


def checksum(str_):
	# In this function we make the checksum of our packet
	str_ = bytearray(str_)
	csum = 0
	countTo = (len(str_) // 2) * 2

	for count in range(0, countTo, 2):
		thisVal = str_[count + 1] * 256 + str_[count]
		csum = csum + thisVal
		csum = csum & 0xffffffff

	if countTo < len(str_):
		csum = csum + str_[-1]
		csum = csum & 0xffffffff

	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
	timeLeft = timeout
	while 1:
		startedSelect = time.time()
		whatReady = select.select([mySocket], [], [], timeLeft)
		howLongInSelect = (time.time() - startedSelect)
		if whatReady[0] == []:  # Timeout
			return "Request timed out."

		timeReceived = time.time()
		recPacket, addr = mySocket.recvfrom(1024)

		icmpHeader = recPacket[20:28]
		# Use the stuct library to unpack the binary encoded data
		# "bbHHh" => char | char | uint | uint | int
		icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
		#print("type: %d  code: %d " %(icmpType, code))
		if type != 8 and packetID == ID:
			bytesInDouble = struct.calcsize("d")
			timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
			return timeReceived - float(timeSent)
		else:
			print("ERR")

		timeLeft = timeLeft - howLongInSelect

		if timeLeft <= 0:
			icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
			print("type: %d  code: %d " % (icmpType, code))
			return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)

	myChecksum = 0
	# Make a dummy header with a 0 checksum.
	# struct -- Interpret strings as packed binary data
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	data = struct.pack("d", time.time())
	# Calculate the checksum on the data and the dummy header.
	myChecksum = checksum(header + data)

	# Get the right checksum, and put in the header
	if sys.platform == 'darwin':
		myChecksum = htons(myChecksum) & 0xffff
	# Convert 16-bit integers from host to network byte order.
	else:
		myChecksum = htons(myChecksum)

	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	packet = header + data
	mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str


# Both LISTS and TUPLES consist of a number of objects
# which can be referenced by their position number within the object

def doOnePing(destAddr, timeout):
	icmp = getprotobyname("icmp")
	# Create Socket here
	mySocket = socket(AF_INET, SOCK_DGRAM, icmp)

	myID = os.getpid() & 0xFFFF  # Return the current process i

	sendOnePing(mySocket, destAddr, myID)
	delay = receiveOnePing(mySocket, myID, timeout, destAddr)
	mySocket.close()
	return delay


def ping(host, timeout=1):
	dest = gethostbyname(host)
	packetLoss = 0
	failedPing = 0
	print("Pinging " + dest + " using Python:")
	print("")
	# Send ping requests to a server separated by approximately one second
	rttList = []
	try:
		delay = doOnePing(dest, timeout)
		if isinstance(delay, str):
			# Failed to reach
			failedPing += 1
			print(delay)
		else:
			packetLoss += 1
			min = delay
			max = delay
			avg = delay
			rttList.append(delay)
			print(str(round(delay * 1000, 3)) + " ms")
			time.sleep(1)
		while 1:
			delay = doOnePing(dest, timeout)
			if isinstance(delay, str):
				# Failed to reach
				failedPing += 1
				print(delay)
				continue
			if max < delay:
				max = delay
			if min > delay:
				min = delay
			if delay > 0:
				packetLoss += 1
			rttList.append(delay)
			print(str(round(delay * 1000, 3)) + " ms")
			time.sleep(1)  # one second
		return delay
	except(KeyboardInterrupt):
		avg = sum(rttList) / len(rttList)
		totalPacketLoss = round(100 - (packetLoss / (packetLoss + failedPing)) * 100, 3)
		min = round(min * 1000, 3)
		avg= round(avg * 1000, 3)
		max = round(max * 1000, 3)
		print("Min: %.3f ms Avg: %.3f ms Max: %.3f ms PacketLoss: %.2f%%" % (min, avg, max, totalPacketLoss))
		return


ping("google.com")
#ping("192.168.57.1")

