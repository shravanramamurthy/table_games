import pygame
from Player import *
from Deck import *
import socket
import threading 
import copy
from queue import Queue

HOST = ""  # put your IP address here if playing on multiple computers
PORT = 50003

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.connect((HOST, PORT))
print("connected to server")


# make sure the dealer stays only if they have won

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


class TableGames(object):
	# initializes the values
	def __init__(self, width=500, height=500):
		self.state = "startScreen"
		self.width = width
		self.height = height
		self.frameRate = 5
		self.me = Player(1)
		self.dealer = Player(0)
		self.deck = Deck()
		self.turnOver = False
		self.dealerTurn = False
		self.gameOver = False
		self.roundOver = False
		self.trueBlackjack = False
		self.PID = 2
		self.roundOverMessage = ""
		self.bet = 10
		self.placeBet = True
		self.playerWon = False
		self.takeMoney = False
		self.firstHand = True
		self.handOver = False
		self.drawCard = False
		self.showHand = False
		self.cont = False
		self.river = False
		self.turn = False
		self.otherStrangers = dict()
		self.allPlayers = dict()
		self.tableCards = Player(99)
		self.pot = 0
		self.call = 0

	# calls each respective timer Fired methods as needed
	def timerFired(self):

		if self.state == "blackjackScreen":
			self.blackjackTimerFired()
		elif self.state == "pokerScreen":
			self.pokerTimerFired()

	# blackjack timreFired checks a variety of conditions
	def blackjackTimerFired(self):
		# this will parse the commands that the user has sent to the other users
		# in the game.
		while (serverMsg.qsize() > 0):
			msg = serverMsg.get(False)
			try:
				print("received: ", msg, "\n")
				msg = msg.split()
				command = msg[0]
				if (command == "myIDis"):
					myPID = msg[1]
					self.me.changePID(myPID)
				elif (command == "newPlayer"):
					newPID = msg[1]
					self.otherStrangers[newPID] = Player(self.PID)
					self.PID += 1
				elif (command == "Card"):
					PID = msg[1]
					value = int(msg[2])
					suit = msg[4]
					card = Card(suit, value)
					self.deck.removeCard(card)
				elif (command == "Dealer"):
					PID = msg[1]
					value = int(msg[2])
					suit = msg[4]
					card = Card(suit, value)
					self.dealer.addCard(card)
					self.deck.removeCard(card)
				elif (command == "Turn"):
					self.otherStrangers[msg[1]].turnOver = True
			except:
				print("failed")
			serverMsg.task_done()

		msg1 = ""
		msg2 = ""
		# checks to make sure the game or the round isn't over
		if not self.gameOver:
			if not self.roundOver:
				# checks the dealer turn and not time to place a bet
				if not self.dealerTurn:
					if not self.placeBet:
						# deals the card if there is the bet is already in
						if len(self.me.getCards()) < 2:
							card = self.deck.drawCard()
							self.me.addCard(card)
							msg1 = "Card " + card.__repr__() + "\n"
						# also gives the dealer the cards
						if len(self.dealer.getCards()) < 2:
							card = self.deck.drawCard()
							self.dealer.addCard(card)
							msg2 = "Dealer " + card.__repr__() + "\n"
						# always check if there is a legal blackjack move to make
						if not self.checkLegalBlackjack(self.me)[0]:
							# the user can't do anything anymore, and the dealer will take
							# the money away and show him the cards
							self.me.turnOver = True
							self.turnOver = True
							self.dealerTurn = True
							message = "Turn " + "\n"
							print("sending: ", message)
							self.server.send(message.encode())

							gameOn = True
							for i in self.otherStrangers:
								if self.otherStrangers[i].turnOver == False:
									gameOn = False
									break
							if gameOn:
								self.roundOver = True
								self.takeMoney = True
								self.roundOverMessage = "Dealer Wins!"
								self.me.turnOver = True
								self.dealerTurn = True
								self.turnOver = True
						if self.me.turnOver:
							gameOn = True
							for i in self.otherStrangers:
								if self.otherStrangers[i].turnOver == False:
									gameOn = False
									break
							if gameOn:
								self.dealerTurn = True
								self.startDealerMove()

							self.me.value = self.checkLegalBlackjack(self.me)[1]
				else:
					# starts the dealer portion of the move making
					self.startDealerMove()
			else:
				# decides how to reapportion the money for the user
				if self.playerWon and self.takeMoney:
					self.roundOverMessage = "Player Wins!"
					self.me.money += self.bet
					self.takeMoney = False
				elif not self.playerWon and self.takeMoney:
					self.roundOverMessage = "Dealer Wins!"
					self.me.money -= self.bet
					self.takeMoney = False
					# stops the game if the user has lsot
					if self.me.money == 0:
						self.gameOver = True
		# send the message to other players!
		if (msg1 != ""):
			print("sending: ", msg1, )
			self.server.send(msg1.encode())
		if (msg2 != ""):
			print("sending: ", msg2, )
			self.server.send(msg2.encode())

	def pokerTimerFired(self):
		# this will parse the commands that the user has sent to the other users
		# in the game.
		if self.me.money == 0 and self.roundOver: self.gameOver = True
		while (serverMsg.qsize() > 0):
			msg = serverMsg.get(False)
			try:
				print("received: ", msg, "\n")
				msg = msg.split()
				command = msg[0]

				if (command == "myIDis"):
					myPID = msg[1]
					self.me.changePID(myPID)

				elif (command == "newPlayer"):
					newPID = msg[1]
					self.otherStrangers[newPID] = Player(self.PID)
					self.PID += 1
				elif (command == "Card"):
					PID = msg[1]
					value = int(msg[2])
					suit = msg[4]
					card = Card(suit, value)
					self.deck.removeCard(card)
				elif (command == "Table"):
					PID = msg[1]
					value = int(msg[2])
					suit = msg[4]
					card = Card(suit, value)
					self.tableCards.addCard(card)
					self.deck.removeCard(card)
				elif (command == "Pot"):
					value = int(msg[2])
					bet = value - self.pot
					self.me.bet = bet
					self.pot = value
					player = msg[1]
					self.otherStrangers[player].turnOver = True
				elif (command == "Total"):
					value = int(msg[2])
					player = msg[1]
					self.takeMoney = True
					self.otherStrangers[player].total = value
				elif (command == "Done"):
					player = msg[1]
					del self.otherStrangers[player]
			except:
				print("failed")
			serverMsg.task_done()
		cardMsg1 = ""
		cardMsg2 = ""
		cardMsg3 = ""
		# checks if the game and round is over for that turn
		if not self.gameOver:
			if not self.roundOver:
				# gives the user two cards for the hand
				if len(self.me.getCards()) < 2:
					card1 = self.deck.drawCard()
					card2 = self.deck.drawCard()
					self.me.addCard(card1)
					self.me.addCard(card2)
					self.server.send(("Card " + card1.__repr__() + "\n").encode())
					self.server.send(("Card " + card2.__repr__() + "\n").encode())
				gameOn = True
				# checks to see whether the user has placed a bet for that hand.
				if not self.placeBet:
					for i in self.otherStrangers:
						if not self.otherStrangers[i].turnOver:
							gameOn = False
							break
					if not self.me.turnOver:
						gameOn = False
					# time to draw
					# the cards for the table
					if gameOn:
						if self.drawCard:
							# makes sure only 5 cards are ever on the table
							if len(self.tableCards.getCards()) < 5:
								# this draws up the flop in the card
								if len(self.tableCards.getCards()) < 3:
									card = self.deck.drawCard()
									self.tableCards.addCard(card)
									cardMsg1 = "Table " + card.__repr__() + "\n"
									card = self.deck.drawCard()
									self.tableCards.addCard(card)
									cardMsg2 = "Table " + card.__repr__() + "\n"
									card = self.deck.drawCard()
									self.tableCards.addCard(card)
									cardMsg3 = "Table " + card.__repr__() + "\n"
									self.drawCard = False
								self.drawCard = False
								self.placeBet = True
								self.me.turnOver = False

								if self.cont == True:
									self.turn = True
								self.cont = True if not self.turn else False

								if self.turn:
									card = self.deck.drawCard()
									self.tableCards.addCard(card)
									cardMsg1 = "Table " + card.__repr__() + "\n"

								for i in self.otherStrangers:
									self.otherStrangers[i].turnOver = False
							else:
								self.river = True
								self.me.turnOver = False
								for i in self.otherStrangers:
									self.otherStrangers[i].turnOver = False
								self.placeBet = True
							if self.showHand:
								# checks the hands of everyone at the table.
								self.roundOverMessage = self.checkLegalPoker(self.me)[0]
								self.me.total = int(self.checkLegalPoker(self.me)[1])
								message = "Total " + str(self.me.total) + "\n"
								print("sending: ", message, )
								self.server.send(message.encode())
								self.playerWon = True
								self.roundOver = True
							# if self.takeMoney:
							# 	for i in self.otherStrangers:
							# 		if self.otherStrangers[i].getTotal() > self.me.total:
							# 			self.playerWon = False
							# if self.playerWon: self.me.money += self.pot
			self.playerWonMessage = ""
			if self.takeMoney:
				for i in self.otherStrangers:
					if self.otherStrangers[i].total > self.me.total:
						self.playerWon = False
				if self.playerWon:
					self.me.money += self.pot
					self.takeMoney = False
					self.playerWonMessage = "You Won!"
				else:
					self.playerWonMessage = "You Lost :("
		if cardMsg1 != "":
			print("sending: ", cardMsg1, )
			self.server.send(cardMsg1.encode())

		if cardMsg2 != "":
			print("sending: ", cardMsg2, )
			self.server.send(cardMsg2.encode())

		if cardMsg3 != "":
			print("sending: ", cardMsg3, )
			self.server.send(cardMsg3.encode())

	# redraws everything based on what state the user is in
	def redrawAll(self, screen):
		if self.state == "startScreen":
			self.redrawStartScreen(screen)
		elif self.state == "blackjackScreen":
			self.redrawBlackjackScreen(screen)
		elif self.state == "pokerScreen":
			self.redrawPokerScreen(screen)

	def redrawStartScreen(self, screen):
		# draws the start screen and displays the instructions
		color = (255, 250, 240)
		pygame.draw.rect(screen, color, pygame.Rect(0, 0, self.width, self.height))
		pygame.display.set_caption(self.state)
		pygame.font.init()
		font = pygame.font.SysFont('apple chancery', 24)
		message1 = "Welcome to Casino de Shravan"
		message2 = "We have a couple table games for you to play today."
		message3 = "Press 'p' to play poker or 'b' to play blackjack."
		message4 = "You can also press the icons below to play their"
		message5 = "respective game. "
		text = font.render(message1, 1, (0, 0, 0,))
		screen.blit(text, (self.width / 4, 20))
		text = font.render(message2, 1, (0, 0, 0,))
		screen.blit(text, (self.width / 4, 50))
		text = font.render(message3, 1, (0, 0, 0,))
		screen.blit(text, (self.width / 4, 80))
		text = font.render(message4, 1, (0, 0, 0,))
		screen.blit(text, (self.width / 4, 110))
		text = font.render(message5, 1, (0, 0, 0,))
		screen.blit(text, (self.width / 4, 140))
		path = "images/poker.png"
		image = pygame.transform.rotate(pygame.transform.scale(
			pygame.image.load(path).convert_alpha(), (200, 200)), 0)  # rotate
		screen.blit(image, (self.width / 4, self.height * .25))
		path = "images/blackjack.png"
		image = pygame.transform.rotate(pygame.transform.scale(
			pygame.image.load(path).convert_alpha(), (200, 200)), 0)  # rotate
		screen.blit(image, (self.width * .6, self.height * .25))

	def redrawBlackjackScreen(self, screen):
		color = (0, 100, 0)
		pygame.display.set_caption(self.state)
		pygame.draw.rect(screen, color, pygame.Rect(0, 0, self.width, self.height))
		# draws the game over sign and the main menu button
		if self.gameOver:
			text = pygame.font.SysFont('apple chancery', 60).render("GAME OVER", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width / 2, self.height / 2))
			pygame.draw.rect(screen, (192, 192, 192), (self.width * .42, self.height
																								 * .82, self.width * .25,
																								 self.height * .08))
			text = pygame.font.SysFont('apple chancery', 60).render("Main Menu", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .42, self.height * .83))

		else:
			# draws the initial bet functionality in the bottom left
			if self.placeBet:
				message = "MONEY - " + str(self.me.money)
				text = pygame.font.SysFont('apple chancery', 40).render(message, 1,
																																(0, 0,
																																 0))
				screen.blit(text, (self.width * .07, self.height * .77))
				pygame.draw.rect(screen, (192, 192, 192), (self.width * .07, self.height
																									 * .82, self.width * .03,
																									 self.height * .05))
				text = pygame.font.SysFont('apple chancery', 50).render("+", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .075, self.height * .82))
				pygame.draw.rect(screen, (192, 192, 192), (self.width * .07, self.height
																									 * .89, self.width * .03,
																									 self.height * .05))
				text = pygame.font.SysFont('apple chancery', 50).render("-", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .077, self.height * .9))

				pygame.draw.rect(screen, (192, 192, 192), (self.width * .12, self.height
																									 * .82, self.width * .07,
																									 self.height * .05))
				font = 50
				if self.bet >= 100:
					font = 40
				text = pygame.font.SysFont('apple chancery', font).render(str(self.bet),
																																	1,
																																	(0, 0, 0))
				screen.blit(text, (self.width * .13, self.height * .825))

				pygame.draw.rect(screen, (30, 144, 255), (self.width * .12, self.height
																									* .89, self.width * .07,
																									self.height * .05))
				text = pygame.font.SysFont('apple chancery', 18).render("PLACE BET", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .122, self.height * .905))

				pygame.draw.rect(screen, (255, 0, 0), (self.width * .2, self.height
																							 * .85, self.width * .07,
																							 self.height * .05))
				text = pygame.font.SysFont('apple chancery', 18).render("ALL IN", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .202, self.height * .875))


			else:
				# this will cycle through the user cards and draw the cards that the
				# usr has
				x = self.width * 0.35
				y = self.height * 0.75
				for i in self.me.getCards():
					path = "images/" + i.getCardImage() + ".png"
					image = pygame.transform.rotate(pygame.transform.scale(
						pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
					screen.blit(image, (x, y))
					x += self.width * .05

				# draws the dealer cards and based on whether it's the dealer's turn,
				#  will draw either a flipped card or both cards facing the user.
				x = self.width * 0.35
				y = self.height * .15
				# the scaling was used with help from the gitbook manual on 15-112
				# website for pygame
				if self.turnOver:
					for i in self.dealer.getCards():
						path = "images/" + i.getCardImage() + ".png"
						# this scaling idea was given from a github manual
						image = pygame.transform.rotate(pygame.transform.scale(
							pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
						screen.blit(image, (x, y))
						x += self.width * 0.05
				else:
					# draws the images like above.
					if len(self.dealer.getCards()) > 0:
						path = "images/" + self.dealer.cards[0].getCardImage() + ".png"
						image = pygame.transform.rotate(pygame.transform.scale(
							pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
						screen.blit(image, (x, y))
						path = "images/red_back.png"
						image = pygame.transform.rotate(pygame.transform.scale(
							pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
						screen.blit(image, (x * 1.15, y))

				pygame.draw.rect(screen, (192, 192, 192), (self.width * .75, self.height
																									 * .75, self.width * .1,
																									 self.height * .08))
				pygame.draw.rect(screen, (255, 0, 0), (self.width * .75, self.height *
																							 .85, self.width * .1,
																							 self.height *
																							 .08))
				# draws the functionality that will appear in the lower right hand
				# corner that the user can use to interact with the game.
				text = pygame.font.SysFont('apple chancery', 30).render("DEALER", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .25, self.height * .23))
				text = pygame.font.SysFont('apple chancery', 30).render("PLAYER", 1, (0,
																																							0,
																																							0))
				screen.blit(text, (self.width * .25, self.height * .83))
				text = pygame.font.SysFont('apple chancery', 30).render("HIT", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .77, self.height * .77))
				text = pygame.font.SysFont('apple chancery', 30).render("STAY", 1,
																																(0, 0,
																																 0))
				screen.blit(text, (self.width * .77, self.height * .87))
			# display game over message
			if self.roundOver:
				text = pygame.font.SysFont('apple chancery', 50).render(
					self.roundOverMessage, 1,
					(0, 0, 0))
				screen.blit(text, (self.width * .3, self.width * .4))
				pygame.draw.rect(screen, (192, 192, 192), (self.width * .75, self.height
																									 * .75, self.width * .17,
																									 self.height * .08))
				pygame.draw.rect(screen, (0, 100, 0), (self.width * .75, self.height *
																							 .85, self.width * .15,
																							 self.height *
																							 .08))
				text = pygame.font.SysFont('apple chancery', 30).render("NEW ROUND", 1,
																																(0, 0, 0))
				screen.blit(text, (self.width * .77, self.height * .77))

	def redrawPokerScreen(self, screen):
		color = (0, 100, 0)
		pygame.display.set_caption(self.state)
		pygame.draw.rect(screen, color, pygame.Rect(0, 0, self.width, self.height))
		# draw the game over screen
		if self.gameOver:
			text = pygame.font.SysFont('apple chancery', 60).render("GAME OVER", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width / 3, self.height / 2))
			pygame.draw.rect(screen, (192, 192, 192), (self.width * .42, self.height
																								 * .82, self.width * .25,
																								 self.height * .08))
			text = pygame.font.SysFont('apple chancery', 60).render("Main Menu", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .42, self.height * .83))
		elif self.roundOver:
			text = pygame.font.SysFont('apple chancery', 50).render(
				self.roundOverMessage, 1,
				(0, 0, 0))
			screen.blit(text, (self.width * .3, self.width * .4))
			text = pygame.font.SysFont('apple chancery', 50).render(
				self.playerWonMessage, 1, (0, 0, 0))
			screen.blit(text, (self.width * .3, self.width * .5))
			pygame.draw.rect(screen, (192, 192, 192), (self.width * .75, self.height
																								 * .75, self.width * .17,
																								 self.height * .08))
			pygame.draw.rect(screen, (0, 100, 0), (self.width * .75, self.height *
																						 .85, self.width * .15,
																						 self.height *
																						 .08))
			text = pygame.font.SysFont('apple chancery', 30).render("NEW ROUND", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .77, self.height * .77))
		else:
			# draws the cards that the user has
			x = self.width * 0.35
			y = self.height * 0.75
			for i in self.me.getCards():
				path = "images/" + i.getCardImage() + ".png"
				image = pygame.transform.rotate(pygame.transform.scale(
					pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
				screen.blit(image, (x, y))
				x += self.width * .05
			# draw the cards that is on the table
			x = self.width * 0.15
			y = self.height * .4
			if self.cont:
				for i in range(0, 3):
					path = "images/" + self.tableCards.getCards()[i].getCardImage() + \
								 ".png"
					image = pygame.transform.rotate(pygame.transform.scale(
						pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
					screen.blit(image, (x, y))
					x += self.width * .15
			x = self.width * 0.15
			y = self.height * .4
			if self.turn and not self.cont:
				for i in range(0, 4):
					path = "images/" + self.tableCards.getCards()[i].getCardImage() + \
								 ".png"
					image = pygame.transform.rotate(pygame.transform.scale(
						pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
					screen.blit(image, (x, y))
					x += self.width * .15
			x = self.width * 0.15
			y = self.height * .4
			if self.river:
				for i in range(0, 5):
					path = "images/" + self.tableCards.getCards()[i].getCardImage() + \
								 ".png"
					image = pygame.transform.rotate(pygame.transform.scale(
						pygame.image.load(path).convert_alpha(), (132, 178)), 0)  # rotate
					screen.blit(image, (x, y))
					x += self.width * .15
			# draws the buttons in the bottom left corner that the user can
			# interact with
			message = "MONEY - " + str(self.me.money)
			text = pygame.font.SysFont('apple chancery', 40).render(message, 1, (0, 0,
																																					 0))
			screen.blit(text, (self.width * .07, self.height * .77))
			pygame.draw.rect(screen, (192, 192, 192), (self.width * .07, self.height
																								 * .82, self.width * .03,
																								 self.height * .05))
			text = pygame.font.SysFont('apple chancery', 50).render("+", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .075, self.height * .82))
			pygame.draw.rect(screen, (192, 192, 192), (self.width * .07, self.height
																								 * .89, self.width * .03,
																								 self.height * .05))
			text = pygame.font.SysFont('apple chancery', 50).render("-", 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .077, self.height * .9))

			pygame.draw.rect(screen, (192, 192, 192), (self.width * .12, self.height
																								 * .82, self.width * .07,
																								 self.height * .05))
			text = pygame.font.SysFont('apple chancery', 50).render(str(self.bet), 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .132, self.height * .825))

			pygame.draw.rect(screen, (30, 144, 255), (self.width * .12, self.height
																								* .89, self.width * .07,
																								self.height * .05))
			if self.bet > self.call or self.firstHand:
				text = pygame.font.SysFont('apple chancery', 40).render("BET", 1,
																																(0, 0, 0))
			else:
				text = pygame.font.SysFont('apple chancery', 35).render("CALL", 1,
																																(0, 0, 0))
			screen.blit(text, (self.width * .122, self.height * .905))
			message = "POT - " + str(self.pot)
			text = pygame.font.SysFont('apple chancery', 40).render(message, 1,
																															(0, 0, 0))
			screen.blit(text, (self.width * .4, self.height * .3))
		# pygame.draw.rect(screen, (255, 0, 0), (self.width * .2, self.height
		# 																			 * .85, self.width * .07,
		# 																			 self.height * .05))
		# text = pygame.font.SysFont('apple chancery', 18).render("ALL IN", 1,
		# 																												(0, 0, 0))
		# screen.blit(text, (self.width * .202, self.height * .875))
		# pygame.draw.rect(screen, (255, 0, 0), (self.width * .75, self.height
		# 																			 * .75, self.width * .1,
		# 																			 self.height * .08))
		# message = "FOLD"
		# text = pygame.font.SysFont('apple chancery', 40).render(message, 1,
		# 																												(0, 0, 0,))
		# screen.blit(text, (self.width * .75, self.height * .77))

	# calls the relevant key pressed as needed.
	# ALl key presses will do the same funcitonalty, either go back to the home
	#  screen quit the game.
	def keyPressed(self, keyCode, modifier):
		if self.state == "startScreen":
			self.startScreenKeyPressed(keyCode, modifier)
		elif self.state == "blackjackScreen":
			self.blackjackScreenKeyPressed(keyCode, modifier)
		elif self.state == "pokerScreen":
			self.pokerScreenKeyPressed(keyCode, modifier)

	def startScreenKeyPressed(self, keyCode, modifier):
		if keyCode == pygame.K_p:
			self.state = "pokeow to rScreen"
		if keyCode == pygame.K_b:
			self.state = "blackjackScreen"
			self.allPlayers = copy.deepcopy(self.otherStrangers)
		if keyCode == pygame.K_q:
			self.done = True
			pygame.quit()

	def blackjackScreenKeyPressed(self, keyCode, modifier):
		if keyCode == pygame.K_q:
			self.deck = Deck()
			self.me.clearCards()
			self.tableCards.clearCards()
			self.bet = 10
			self.placeBet = True
			self.playerWon = False
			self.takeMoney = False
			self.firstHand = True
			self.handOver = False
			self.drawCard = False
			self.showHand = False
			self.roundOver = False
			self.roundOverMessage = ""
			self.playerWonMessage = ""
			self.me.turnOver = False
			for i in self.otherStrangers:
				self.otherStrangers[i].turnOver = False
			self.cont = False
			self.river = False
			# self.otherStrangers = dict()
			# self.otherStrangers = copy.deepcopy(self.allPlayers)
			self.turn = False
			self.pot = 0
			self.call = 0
			self.state = "startScreen"

	def pokerScreenKeyPressed(self, keyCode, modifier):
		if keyCode == pygame.K_q:
			self.deck = Deck()
			self.me.clearCards()
			self.dealer.clearCards()
			self.turnOver = False
			self.me.turnOver = False
			for i in self.otherStrangers:
				self.otherStrangers[i].turnOver = False
			self.dealerTurn = False
			self.roundOver = False
			self.trueBlackjack = False
			self.placeBet = True
			self.playerWon = False
			self.bet = 10
			self.roundOverMessage = ""
			self.state = "startScreen"

	# calls the relevant moused pressed classes.
	def mousePressed(self, x, y):
		if self.state == "startScreen":
			self.startMousePressed(x, y)
		elif self.state == "blackjackScreen":
			self.blackjackMousePressed(x, y)
		elif self.state == "pokerScreen":
			self.pokerMousedPressed(x, y)

	def startMousePressed(self, x, y):
		if x >= self.width / 4 and x <= self.width / 4 + 200 and y >= self.height * \
				.25 and y <= self.height * .25 + 200:
			self.state = "pokerScreen"
		elif x >= self.width * .6 and x <= self.width * .6 + 200 and y >= \
						self.height * .25 and y <= self.height * .25 + 200:
			self.state = "blackjackScreen"

	def blackjackMousePressed(self, x, y):
		# just checks if the user has interacted with the buttons that are being
		# displayed on the screena nd acts occordingly to what the button show.
		# e.g. if the usr hits a new orund button, it will start a new round.
		if not self.gameOver:
			if not self.dealerTurn:
				if self.placeBet:
					if x >= self.width * 0.07 and x <= self.width * 0.1 and y >= \
									self.height * .82 and y <= self.height * .87:
						self.bet += 5
						if self.bet > self.me.money:
							self.bet = self.me.money
					elif x >= self.width * 0.07 and x <= self.width * .1 and y >= \
									self.height * .89 and y <= self.height * .94:
						self.bet -= 5
						if self.bet < 10:
							self.bet = 10
					elif x >= self.width * .12 and x <= self.width * .19 and y >= \
									self.height * .89 and y <= self.height * .94:
						self.placeBet = False
					elif x >= self.width * .2 and x <= self.width * .27 and y >= \
									self.height * .85 and y <= self.height * .9:
						self.bet = self.me.money
				elif x >= self.width * .75 and x <= self.width * .85 and y >= \
								self.height \
								* .75 and y <= self.height * 0.83 and not self.turnOver:
					card = self.deck.drawCard()
					self.me.addCard(card)
					message = "Card " + card.__repr__() + "\n"
					print("sending: ", message)
					self.server.send(message.encode())
				# draw another card
				elif x >= self.width * .75 and x <= self.width * .85 and y >= self.height \
						* .85 and y <= self.height * 0.93:
					self.me.value = self.checkLegalBlackjack(self.me)[1]
					self.turnOver = True
					self.me.turnOver = True
					self.dealerTurn = True
					message = "Turn " + "\n"
					print("sending: ", message)
					self.server.send(message.encode())
					self.startDealerMove()

			if self.roundOver:
				if x >= self.width * .75 and x <= self.width * 0.92 and y >= \
								self.height * 0.75 and y <= self.height * 0.83:
					self.deck = Deck()
					self.me.clearCards()
					self.dealer.clearCards()
					self.turnOver = False
					self.me.turnOver = False
					for i in self.otherStrangers:
						self.otherStrangers[i].turnOver = False
					self.dealerTurn = False
					self.roundOver = False
					self.trueBlackjack = False
					self.placeBet = True
					self.playerWon = False
					self.bet = 10
					self.roundOverMessage = ""
		else:
			if x >= self.width * .42 and x <= self.width * .67 and y >= self.height \
					* 0.82 and y <= self.height * .9:
				self.deck = Deck()
				self.me.clearCards()
				self.tableCards.clearCards()
				self.bet = 10
				self.placeBet = True
				self.playerWon = False
				self.takeMoney = False
				self.firstHand = True
				self.handOver = False
				self.drawCard = False
				self.showHand = False
				self.roundOver = False
				self.roundOverMessage = ""
				self.playerWonMessage = ""
				self.me.turnOver = False
				for i in self.otherStrangers:
					self.otherStrangers[i].turnOver = False
				self.cont = False
				self.river = False
				# self.otherStrangers = dict()
				# self.otherStrangers = copy.deepcopy(self.allPlayers)
				self.turn = False
				self.pot = 0
				self.call = 0

	def pokerMousedPressed(self, x, y):
		# just checks if the user has interacted with the buttons that are being
		# displayed on the screena nd acts occordingly to what the button show.
		# e.g. if the usr hits a new orund button, it will start a new round.
		potMsg = ""
		if not self.gameOver:
			if self.placeBet:
				if x >= self.width * 0.07 and x <= self.width * 0.1 and y >= \
								self.height * .82 and y <= self.height * .87:
					self.bet += 5
					if self.bet > self.me.money:
						self.bet = self.me.money
				elif x >= self.width * 0.07 and x <= self.width * .1 and y >= \
								self.height * .89 and y <= self.height * .94:
					self.bet -= 5
					if self.bet <= 10 and self.money > 10:
						self.bet = 10
				elif x >= self.width * .12 and x <= self.width * .19 and y >= \
								self.height * .89 and y <= self.height * .94:
					self.placeBet = False
					self.call = self.bet
					self.drawCard = True
					self.me.turnOver = True
					self.me.money -= self.bet
					self.pot += self.bet
					self.firstHand = False
					potMsg = "Pot " + str(self.pot) + "\n"
					if self.river:
						self.showHand = True
					# elif x >= self.width * .2 and x <= self.width * .27 and y >= \
					# 				self.height * .85 and y <= self.height * .9:
					# 	self.bet = self.me.money
					# 	self.turn = True
					# 	self.river = True
					# elif x >= self.width * .75 and x <= self.width * .85 and y >= \
					# 				self.height * .75 and y <= self.height * 0.83:
					# 	self.roundOver = True
					# 	message = "Done " + "\n"
					# 	print ("sending: ", message, )
					# 	self.server.send(message.encode())
			if self.roundOver:
				if x >= self.width * .75 and x <= self.width * 0.92 and y >= \
								self.height * 0.75 and y <= self.height * 0.83:
					self.deck = Deck()
					self.me.clearCards()
					self.tableCards.clearCards()
					self.bet = 10
					self.placeBet = True
					self.playerWon = False
					self.takeMoney = False
					self.firstHand = True
					self.handOver = False
					self.drawCard = False
					self.showHand = False
					self.roundOver = False
					self.roundOverMessage = ""
					self.playerWonMessage = ""
					self.me.turnOver = False
					for i in self.otherStrangers:
						self.otherStrangers[i].turnOver = False
					self.cont = False
					self.river = False
					# self.otherStrangers = dict()
					# self.otherStrangers = copy.deepcopy(self.allPlayers)
					self.turn = False
					self.pot = 0
					self.call = 0
		else:
			if x >= self.width * .42 and x <= self.width * .67 and y >= self.height \
					* 0.82 and y <= self.height * .9:
				self.deck = Deck()
				self.me.clearCards()
				self.dealer.clearCards()
				self.turnOver = False
				self.me.turnOver = False
				for i in self.otherStrangers:
					self.otherStrangers[i].turnOver = False
				self.dealerTurn = False
				self.roundOver = False
				self.trueBlackjack = False
				self.placeBet = True
				self.playerWon = False
				self.bet = 10
				self.roundOverMessage = ""
				self.state = "startScreen"

		if (potMsg != ""):
			print("sending: ", potMsg, )
			self.server.send(potMsg.encode())

	def startDealerMove(self):
		# this will start the dealer move and draw a card if they are not already
		#  above 21.
		# they will also stop drawing cards if they are above 17 AND they are
		# also above the suer value
		# they will draw a card if they are above 17 and they are below the user
		# card.
		self.me.turnOver = True
		self.dealerMove = True
		self.turnOver = True
		# self.roundOver = True
		legal, value = self.checkLegalBlackjack(self.dealer)
		if legal:
			if self.me.value > 21:
				self.roundOver = True
				self.playerWon = False
				self.takeMoney = True
				self.roundOverMessage = "Dealer Wins!"
			elif value < 17 or (value >= 17 and value < self.me.value):
				card = self.deck.drawCard()
				self.dealer.addCard(card)
				message = "Dealer " + card.__repr__() + "\n"
				print("sending: ", message, )
				self.server.send(message.encode())
			elif value >= 17 and value > self.me.value:
				# stop
				self.roundOver = True
				self.playerWon = False
				self.takeMoney = True
				self.roundOverMessage = "Dealer Wins!"
			elif value >= 17 and value == self.me.value:
				self.roundOver = True
				self.roundOverMessage = "Push"
		else:
			self.playerWon = True
			self.roundOverMessage = "Player Wins!"
			self.roundOver = True
			self.takeMoney = True

	def checkLegalBlackjack(self, player):
		# this checks to see whether the user is still under 21. This is also
		# adding up the values based on the cards that the user has. This factors
		#  in whether an Ace would be contextually appropriate as a 11 or a 1.
		value = 0
		isAce = False
		for i in player.getCards():
			if i.value >= 10 and i.value < 14:
				value += 10
			elif i.value == 14:
				value += 11
				isAce = True
			else:
				value += i.value
			if value > 21:
				if not isAce:
					return (False, value)
				else:
					value -= 10
					isAce = False
				# if value == 21 and len(player.getCards()) == 2:
				# 	self.roundOver = True
				# 	self.playerWon = True
				# 	self.takeMoney = True
				# 	self.roundOverMessage = "True Blackjack!"

		return (True, value)

	def checkLegalPoker(self, player):
		# this is code that was taken off a webiste:
		# https://codereview.stackexchange.com/questions/144551/find-and-display-
		# best-poker-hand
		# this code has been optimized for my game
		# i Take no credit for the code written below.
		# this is the same algorithm that is just chekcing over and over again.
		import itertools

		def numeric_ranks(cards):
			"""
			Changes the input list of card strings to a list of
			strings with numbers substituting for face cards.
			ex.
			numeric_ranks(['AS','3S','4S','5S','JC'])
			returns ['14S','3S','4S','5S','11C']
			"""
			suits = get_suits(cards)
			face_numbers = {'A': 14, 'J': 11, 'Q': 12, 'K': 13}
			for index, card in enumerate(cards):
				rank = card[0:-1]
				try:
					int(rank)
				except:
					# Rank is a letter, not a number
					cards[index] = str(face_numbers[rank]) + suits[index]
			return cards

		def get_ranks(cards):
			"""
			Returns a list of ints containing the rank of each card in cards.
			ex.
			get_ranks(['2S','3C','5C','4D','6D'])
			returns [2,3,5,4,6]
			"""
			# cards = numeric_ranks(
			# 	cards)  # Convert rank letters to numbers (e.g. J to 11)
			return [int(card[0:-1]) for card in cards]

		def get_suits(cards):
			"""
			Returns a list of strings containing the suit of each card in cards.
			ex.
			get_ranks(['2S','3C','5C','4D','6D'])
			returns ['S','C','C','D','D']
			"""
			return [card[-1] for card in cards]

		def evaluate_hand(hand):
			"""
			Returns a string containing the name of the hand in poker.
			Input hand must be a list of 5 strings.
			ex.
			evaluate_hand(['2S','3C','5C','4D','6D'])
			returns 'Straight'
			"""
			# hand = numeric_ranks(hand)
			ranks = get_ranks(hand)
			suits = get_suits(hand)
			if len(set(hand)) < len(hand) or max(ranks) > 14 or min(ranks) < 1:
				# There is a duplicate
				return 'Invalid hand'
			if isconsecutive(ranks):
				# The hand is a type of straight
				if all_equal(suits):
					# Hand is a flush
					if max(ranks) == 14:
						# Highest card is an ace
						return 'Royal flush'
					return 'Straight flush'
				return 'Straight'
			if all_equal(suits):
				return 'Flush'
			total = sum([ranks.count(x) for x in ranks])
			hand_names = {
				17: 'Four of a kind',
				13: 'Full house',
				11: 'Three of a kind',
				9: 'Two pair',
				7: 'One pair',
				5: 'High card'
			}
			return (hand_names[total], total)

		def all_equal(lst):
			"""
			Returns True if all elements of lst are the same, False otherwise
			ex.
			all_equal(['S,'S','S']) returns True
			"""
			return len(set(lst)) == 1

		def show_cards(cards):
			""" Prints the rank and suit for each card in cards. """
			cards = sort_cards(cards)
			all_suits = ['C', 'D', 'H', 'S']
			symbols = dict(zip(all_suits, ['\u2667', '\u2662', '\u2661', '\u2664']))
			card_symbols = []
			for card in cards:
				rank = card[0:-1]
				card_symbols.append(rank + symbols[card[-1]])
			return card_symbols

		def isconsecutive(lst):
			"""
			Returns True if all numbers in lst can be ordered consecutively, and False
			otherwise
			"""
			return len(set(lst)) == len(lst) and max(lst) - min(lst) == len(lst) - 1

		def sort_cards(cards):
			"""
			Sorts cards by their rank.
			If rank is a string (e.g., 'A' for Ace), then the rank is changed to a
			number.
			Cards of the same rank are not sorted by suit.
			ex.
			sort_cards(['AS','3S','4S','5S','JC'])
			returns
			['3S','4S','5S','11C','14S']
			"""
			# cards = numeric_ranks(cards)
			rank_list = get_ranks(cards)
			# Keep track of the sorting permutation
			new_order = sorted((e, i) for i, e in enumerate(rank_list))
			unsorted_cards = list(cards)
			for index, (a, b) in enumerate(new_order):
				cards[index] = unsorted_cards[b]
			return cards

		def get_best_hand(cards):
			"""
			Returns the best hand of five cards, from a larger list of cards.
			If ranks are alphabetical (e.g., A for ace), it will convert the rank to a
			number.
			ex.
			get_best_hand(['7C', '7S', '2H', '3C', 'AC', 'AD', '5S'])
			returns
			['5S', '7C', '7S', '14C', '14D']
			"""
			# All combinations of 5 cards from the larger list
			all_hand_combos = itertools.combinations(cards, 5)
			hand_name_list = [
				'Invalid hand',
				'High card',
				'One pair',
				'Two pair',
				'Three of a kind',
				'Straight',
				'Flush',
				'Full house',
				'Four of a kind',
				'Straight flush',
				'Royal flush'
			]
			num_hand_names = len(hand_name_list)
			max_value = 0
			best_hands = {x: [] for x in range(num_hand_names)}
			for combo in all_hand_combos:
				hand = list(combo)
				hand_name = evaluate_hand(hand)[0]  # Get the type of hand (e.g.,
				# one pair)
				try:
					hand_value = hand_name_list.index(hand_name)
				except:
					pass
				if hand_value >= max_value:
					# Stronger or equal hand has been found
					max_value = hand_value
					best_hands[hand_value].append(hand)  # Store hand in dictionary
			max_hand_idx = max(
				k for k, v in best_hands.items() if len(best_hands[k]) > 0)
			rank_sum, max_sum = 0, 0
			# The strongest hand type out of the combinations has been found
			for hand in best_hands[max_hand_idx]:
				# Iterate through hands of this strongest type
				ranks = get_ranks(hand)
				rank_sum = sum(ranks)
				if rank_sum > max_sum:
					max_sum = rank_sum
					best_hand = hand  # Choose hand with highest ranking cards
			return best_hand

		table = [i.getCardImage() for i in self.tableCards.getCards()]
		hand = [i.getCardImage() for i in self.me.getCards()]
		cards = hand + table
		best_hand = get_best_hand(cards)

		show_cards(best_hand)

		return evaluate_hand(best_hand)

	# this method  runs the entire game
	def run(self, server=None, serverMsg=None):
		self.server = server
		self.serverMsg = serverMsg
		pygame.init()
		clock = pygame.time.Clock()
		screen = pygame.display.set_mode((self.width, self.height))
		self.done = False
		while not self.done:
			time = clock.tick(self.frameRate)
			self.timerFired()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.done = True
				elif event.type == pygame.KEYDOWN:
					self.keyPressed(event.key, event.mod)
				elif event.type == pygame.MOUSEBUTTONDOWN:
					self.mousePressed(*(event.pos))
			self.redrawAll(screen)
			pygame.display.flip()

		pygame.quit()


def main():
	# Set up data and call init
	game = TableGames(1000, 900)
	game.run(server, serverMsg)


serverMsg = Queue(100)
threading.Thread(target=handleServerMsg, args=(server, serverMsg)).start()

if __name__ == '__main__':
	main()
