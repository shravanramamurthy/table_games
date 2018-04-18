import socket
import threading
from queue import Queue
from tkinter import *
from Card import *
import random

## get blackjack going
## get poker going
# for tp2: full working game of poker
# for tp3: full working game of blackjack
# for tp1: get the basic animation framework for the game going

HOST = ""  # put your IP address here if playing on multiple computers
PORT = 50004

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.connect((HOST, PORT))
print("connected to server")


def handleServerMsg(server, serverMsg):
	server.setblocking(1)
	msg = ""
	command = ""
	while True:
		msg += server.recv(10).decode("UTF-8")
		command = msg.split("\n")
		while (len(command) > 1):
			readyMsg = command[0]
			msg = "\n".join(command[1:])
			serverMsg.put(readyMsg)
			command = msg.split("\n")


####################################
# customize these functions
####################################

def init(data):
	data.me = Card()
	data.otherStrangers = dict()
	data.gameState = "startScreen"


def keyPressed(event, data):
	if data.gameState == "startScreen":
		startScreenKeyPressed(event, data)
	msg = ""

	# moving
	if event.keysym in ["Up", "Down", "Left", "Right"]:
		if event.keysym == "Up":
			data.me.value += 5
		elif event.keysym == "Down":
			data.me.value -= 5
		elif event.keysym == "Left":
			data.me.value -= 5
		elif event.keysym == "Right":
			data.me.value += 5
		# move myself
		# update message to send
		msg = "Card Changed: " + str(data.me.value) + "\n"

	# send the message to other players!
	if (msg != ""):
		print("sending: ", msg, )
		data.server.send(msg.encode())


def timerFired(data):
	# timerFired receives instructions and executes them
	while (serverMsg.qsize() > 0):
		msg = serverMsg.get(False)
		try:
			print("received: ", msg, "\n")
			msg = msg.split()
			command = msg[0]

			if (command == "myIDis"):
				myPID = msg[1]
				data.me.changePID(myPID)

			elif (command == "newPlayer"):
				newPID = msg[1]
				data.otherStrangers[newPID] = Card()

			elif (command == "Card"):
				PID = msg[1]
				value = int(msg[3])
				print (value)
				# dy = int(msg[3])
				data.otherStrangers[PID].setValue(value)

		except:
			print("failed")
		serverMsg.task_done()


def redrawAll(canvas, data):
	if data.gameState == "startScreen":
		canvas.create_text(100,100, text="Hello")
	elif data.gameState == "pokerScreen":
		redrawPokerScreen(canvas, data)
	elif data.gameState == "blackjackScreen":
		pass

def redrawStartScreen(canvas, data):
	canvas.create_text(100, 100, text="Hello")

def redrawPokerScreen(canvas, data):
	# draw other players
	for playerName in data.otherStrangers:
		canvas.create_text(100, 50, text=data.otherStrangers[playerName])
	# draw me
	canvas.create_text(50, 100, text=data.me)

def redrawBlackjackScreen(canvas, data):
	# draw other players
	for playerName in data.otherStrangers:
		canvas.create_text(100, 50, text=data.otherStrangers[playerName])
	# draw me
	canvas.create_text(50, 100, text=data.me)

def startScreenKeyPressed(event, data):
	if event.keysym == "p":
		data.gameState = "pokerScreen"
	elif event.keysym == "b":
		data.gameState = "blackjackScreen"
	elif event.keysym == "q":
		quit()



####################################
# use the run function as-is
####################################

def run(width, height, serverMsg=None, server=None):
	def redrawAllWrapper(canvas, data):
		canvas.delete(ALL)
		redrawAll(canvas, data)
		canvas.update()

	def keyPressedWrapper(event, canvas, data):
		keyPressed(event, data)
		redrawAllWrapper(canvas, data)

	def timerFiredWrapper(canvas, data):
		timerFired(data)
		redrawAllWrapper(canvas, data)
		# pause, then call timerFired again
		canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)

	# Set up data and call init
	class Struct(object): pass

	data = Struct()
	data.server = server
	data.serverMsg = serverMsg
	data.width = width
	data.height = height
	data.timerDelay = 100  # milliseconds
	init(data)
	# create the root and the canvas
	root = Tk()
	canvas = Canvas(root, width=data.width, height=data.height)
	canvas.pack()
	# set up events
	root.bind("<Key>", lambda event:
	keyPressedWrapper(event, canvas, data))
	timerFiredWrapper(canvas, data)
	# and launch the app
	root.mainloop()  # blocks until window is closed
	print("bye!")


serverMsg = Queue(100)
threading.Thread(target=handleServerMsg, args=(server, serverMsg)).start()

run(200, 200, serverMsg, server)
