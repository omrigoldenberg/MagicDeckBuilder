from collections import Iterable


class Card:
	def __init__(self, name, link, image, types, legality, ci):
		self.name = name
		self.link = link
		self.image = image
		self.types = types.split()
		self.legality = legality
		self.ci = ci

def check_list(deck_list, t_format, copies=4):
	names = {}
	for quantity, card in deck_list:
		is_basic = False
		for x in card.types:
			if x.startswith("Basic"):
				is_basic = True
		if t_format not in card.legality:
			return False
		n = card.name
		if n not in names:
			names[n] = quantity
		else:
			names[n] += quantity
		if not is_basic and names[n] > copies:
			return False
	return True


# Color identity of a colorless card is empty in scryfall.
def subset(a: list, b: list):
	for item in b:
		if item not in a:
			return False
	return True

def union(x: Iterable[Iterable]):
	c = set()
	for list_x in x:
		for item in list_x:
			c.add(item)
	d = []
	for item in c:
		d.append(item)
	return d


def check_color_identity(deck_list : Iterable[Card], compare):
	for card in deck_list:
		if not subset(compare, card.ci):
			return False
	return True

def extract(c):
	a, b = c
	return b

class Deck:
	def check(self):
		if self.format == 'commander':
			if not self.legality_check(self.format, main=99, side=1):
				return False
			return self.color_check()
		else:
			return self.legality_check(self.format)

	def color_check(self):
		color_identity = union(map(extract, self.sideboard))
		return check_color_identity(map(extract, self.main_deck), color_identity)

	# Returns dictionaries with main and sideboard
	def to_dict(self):
		main = {}
		for (count, card) in self.main_deck:
			main[card] = count
		side = {}
		for (count, card) in self.sideboard:
			side[card] = count
		return main, side

	def __init__(self, name, main_deck, sideboard, t_format):
		self.name: str = name
		self.main_deck: list[(int, Card)] = main_deck
		self.sideboard: list[(int, Card)] = sideboard
		self.format: str = t_format


	def __repr__(self):
		r = self.name + ' for ' + self.format + '\nMainboard:\n'
		for quant, card in self.main_deck:
			r += repr(quant) + 'x ' + card.name + '\n'
		r += '\nSideboard:\n'
		for quant, card in self.sideboard:
			r += repr(quant) + 'x ' + card.name + '\n'
		return r

	def legality_check(self, t_format, main=60, side=15, copies=4):
		main_len = 0
		for card in self.main_deck:
			main_len += card[0]
		side_len = 0
		for card in self.sideboard:
			side_len += card[0]
		if main_len < main:
			#print(1)
			return False
		if side_len > side:
			#print(2)
			return True
		if not check_list(self.main_deck, t_format, copies=copies):
			print(3)
			#return False
		if not check_list(self.sideboard, t_format, copies=copies):
			#print(4)
			return False
		return True

class Guide:

	def __init__(self, side_in: list[tuple[int, Card]], side_out: list[tuple[int, Card]], message: str):
		self.from_side: list[tuple[int, Card]] = side_in
		self.to_side: list[tuple[int, Card]] = side_out
		self.msg: str = message
		self.up = {}
		self.down = {}

	def validate(self, d: Deck):
		main, side = d.to_dict()
		for (quant, card) in self.from_side:
			if card not in side:
				return False
			elif quant > side[card]:
				return False

		for (quant, card) in self.to_side:
			if card not in main:
				return False
			elif quant > main[card]:
				return False
		return True



class GuideHold:
	def __init__(self):
		self.list: list[Guide] = []

	def add(self, g: Guide):
		self.list.append(g)

	def remove(self, g: Guide):
		self.list.remove(g)

	def clear(self):
		self.list = []
		
	def get(self, index: int) -> Guide:
		return self.list[index]

	def valid(self, d: Deck) -> list[Guide]:
		v = []
		for guide in self.list:
			if guide.validate(d):
				v.append(guide)
		return v
