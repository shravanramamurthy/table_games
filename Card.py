import random


class Card(object):
	# IDEA: Remove the card from the pack when you call the method

	def __init__(self, suit, value, PID=""):
		# choose the random card and create a card based on that
		# Card attributes:
		# self.PID = PID
		self.suit = suit
		self.value = value
		self.cardImage = str(self.value) + self.suit[0].upper()

	def __repr__(self):
		if self.value == 15:
			return "%s of %s" % ("Ace", self.suit)
		return "%d of %s" % (self.value, self.suit)

	def getValue(self):
		return self.value

	def getSuit(self):
		return self.suit

	def setValue(self, value):
		self.value = value

	def getCardImage(self):
		return self.cardImage
