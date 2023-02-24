# Python program to implement client side of chat room.
import random
import socket
import sys
import re
import time
import traceback
import threading


class TCP():

	def __init__(self, *args, **kwargs):
		self.client = None
		self.screenName = None
		self.ipaddr = None
		self.port = None
		self.UDPPort = str(random.randint(1025, 65000))
		self.bufferSize = 2048
		self.socketTimeout = 2  # socket timeout in seconds
		self.TCPmsg = ''
		self.stop = False
		self.clientList = []

	def setMessages(self):
		self.HELO = "HELO " + self.screenName + " " + self.ipaddr + " " + self.UDPPort + "\n"
		self.EXIT = "EXIT\n"
		self.RECV = None

	def getUserInput(self):
		if len(sys.argv) != 4:
			print("Correct usage: <screen name>, <server hostname>, <TCP port number>")
			exit()
		self.screenName = str(sys.argv[1])  # unique per user
		self.ipaddr = str(sys.argv[2])  # 127.0.0.1
		self.port = int(sys.argv[3])  # TCP port 8080 the same for all clients
		self.setMessages()

	def connectToServer(self):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((self.ipaddr, self.port))
		self.client.send(self.HELO.encode())
		self.client.settimeout(self.socketTimeout)
		while True:
			try:
				self.TCPmsg += self.client.recv(self.bufferSize).decode()
			except socket.timeout:
				print(traceback.format_exc())
				print("TCP socket timed out connecting to server")
				exit(-1)
			if self.TCPmsg.endswith("\n"):
				break
			else:
				continue

		# If the screen name is taken then notify and exit
		if self.TCPmsg.startswith("RJCT"):
			print("Username: " + self.screenName + " already exist!")
			exit(-1)

		self.TCPmsg = self.TCPmsg[5:]
		pattern = re.compile("(\w+)\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s(\d{1,5})")
		identities = re.findall(pattern, self.TCPmsg)
		self.parseGreeting(identities)
		return self.clientList

	def parseGreeting(self, listOfUsersData):

		for user in listOfUsersData:
			dic = {}
			dic["User"] = user[0]
			dic["IP"] = user[1]
			dic["UDPPort"] = user[2]
			self.clientList.append(dic)
			del dic

	def sendExit(self):
		self.client.send(self.EXIT.encode())

	def __del__(self):
		# Clean up
		self.client.close()




class UDP:
	def __init__(self):
		self.UDPPort = None
		self.ipaddr = None
		self.UDPClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.stop = None
		self.screenName = None
		self.addressAndPort = None
		self.bufferSize = 2048
		self.exit = False
		self.exitPattern = re.compile("EXIT\s(\w+)")  # user is all we need
		self.msgPattern = re.compile("MESG\s(\w+)\s(.*)")  # get the user and the message sent
		self.joinPattern = re.compile("JOIN\s(\w+)\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s(\d{1,5})")
		self.users = []

	def sendMsg(self, msg):
		m = "MESG " + self.screenName + " " + msg + "\n"
		m = m.encode()
		for user in self.users:
			addrAndPort = (user["IP"], int(user["UDPPort"]))
			self.UDPClient.sendto(m, addrAndPort)

	# trim off whitespace
	def addUser(self, joinMsg):
		newUser = re.match(self.joinPattern, joinMsg)
		dic = {"User": newUser.group(1), "IP": newUser.group(2), "UDPPort": newUser.group(3)}
		self.users.append(dic)
		print("Welcome " + newUser.group(1) + " to the chatroom")
		del dic

	def deleteUser(self, deleteMsg):
		userToDelete = re.findall(self.exitPattern, deleteMsg)
		if len(userToDelete) < 1:
			return -1
		userToDelete = userToDelete[0]
		if (userToDelete == self.screenName):
			print(userToDelete + " has left the chat")
			return
		for index, user in enumerate(self.users):
			if user["User"] == userToDelete:
				print(user["User"] + " has left the chat")
				break
		self.users.pop(index)

	def waitForMessage(self):
		self.addressAndPort = (self.ipaddr, int(self.UDPPort))
		self.UDPClient.bind(self.addressAndPort)
		time.sleep(0.01)
		initialWelcome, server = self.UDPClient.recvfrom(self.bufferSize)
		initialWelcome = initialWelcome.decode()  # This is to avoid adding ourselves twice
		initalJoin = re.match(self.joinPattern, initialWelcome)
		if (initalJoin):
			print("Welcome " + initalJoin.group(1) + " to the chatroom")  # Remember to print to the console
		try:
			while True:
				data, server = self.UDPClient.recvfrom(self.bufferSize)
				dataStr = data.decode()
				if dataStr.startswith("MESG"):
					userMsg = re.match(self.msgPattern, dataStr)
					usr = userMsg.group(1)
					if (usr == self.screenName):
						# Dont print your own message
						continue
					msg = userMsg.group(2)
					print(usr + ": " + msg)
				elif dataStr.startswith("JOIN"):
					self.addUser(dataStr)
				elif dataStr.startswith("EXIT"):
					self.deleteUser(dataStr)

		except OSError:
			pass
		except Exception as e:
			print("Unknown Exception occured")
			print(e.with_traceback())

	def getConsoleInput(self):
		while True:
			try:
				console = input()
				if console.startswith("EXIT"):
					break
				self.sendMsg(console)
				self.UDPClient.sendto(console.encode(), self.addressAndPort)
			except EOFError:
				print("Control-D Pressed")
				break
			except KeyboardInterrupt:
				# self.exit = True
				print("Control-C Pressed")
				break
		return

	def __del__(self):
		return

	def __exit__(self):
		return


def main():
	tcp = TCP()
	udp = UDP()
	tcp.getUserInput()
	udp.users = tcp.connectToServer()
	udp.ipaddr = tcp.ipaddr
	udp.screenName = tcp.screenName
	udp.UDPPort = tcp.UDPPort

	t1 = threading.Thread(target=udp.waitForMessage, args=(), daemon=True)
	t1.start()
	udp.getConsoleInput()
	tcp.sendExit()
	time.sleep(0.05)
	udp.UDPClient.close()


if __name__ == '__main__':
	main()
