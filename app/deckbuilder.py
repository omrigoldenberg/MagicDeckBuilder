# Deckbuilder stuff.
import json
import time
from typing import Iterable

from requests import post

from app.classes import Card, Deck


def check_cards(l, lcards):
	for card1 in l:
		check = 0
		for card2 in lcards:
			if card1[1].name == card2[1].name:
				check = 1
				if card1[0] > card2[0]:
					return True
		if check == 0:
			return True
	return False


def get_sb(out_data, deck, side):
	list_out = out_data.split('\n')
	name_out = []
	count_out = []
	for line in list_out:
		split: list[str] = line.split(maxsplit=1)
		count: int = int(split[0])
		name: str = split[1]
		name_out.append(name)
		count_out.append(count)
	cards_out_temp, notfound = request_list(name_out)
	if len(notfound) > 0:
		return None
	cards_out = [card_process(x) for x in cards_out_temp]
	out = [(count_out[i], cards_out[i]) for i in range(len(cards_out))]
	error = False
	if side:
		error = check_cards(out, deck.sideboard)
	else:
		error = check_cards(out, deck.main_deck)
	if error:
		return None
	else:
		return out


def process_initial_text(iterator: Iterable[str]):
	main = []
	side = []
	names = set()
	use_side = False
	# print(iterator)
	for raw in iterator:
		# print(raw)
		line = raw.strip()
		if len(line) < 1:
			use_side = True
			continue
		split: list[str] = line.split(maxsplit=1)
		count: int = int(split[0])
		name: str = split[1]
		if use_side:
			side.append((count, name))
		else:
			main.append((count, name))
		names.add(name)
	return main, side, list(names)


def deck_to_dict(decklist):
	dictionary = {}
	for count, name in decklist:
		dictionary[name] = (count, None)
	return dictionary


# Assumes names is a scryfall list, containing just output, and not missed.
def match_names(deck: list[(int, str)], names):
	transformed = deck_to_dict(deck)
	for entry in names:
		name = entry['name']
		if name in transformed:
			count = transformed[name][0]
			transformed[name] = (count, entry)

	return transformed


def pipeline(iterator: Iterable[str], name: str, tournament: str) -> Deck:
	try:
		res = input_to_decklist(iterator)
		if res is not None:
			m, s = res
			return decklist_to_deck(m, s, name, tournament)
		else:
			return None
	except IndexError:
		return None


def input_to_decklist(iterator: Iterable[str]):
	main, side, names = process_initial_text(iterator)
	output, not_found = request_list(names)
	if len(not_found) > 0:
		return None
	main_d = match_names(main, output)
	side_d = match_names(side, output)
	return main_d, side_d


def decklist_to_deck(main_d, side_d, name, tournament):
	main = []
	for card, value in main_d.items():
		scry_card = value[1]
		main.append((value[0], card_process(scry_card)))
	side = []
	for card, value in side_d.items():
		scry_card = value[1]
		side.append((value[0], card_process(scry_card)))
	d = Deck(name, main, side, tournament)
	if d.check():
		return d
	else:
		return None


def card_process(card):
	na = card['name']
	li = card['scryfall_uri']
	im = card['image_uris']['normal']
	ty = card['type_line']
	le = []
	for tournament, legality in card['legalities'].items():
		if legality == 'legal':
			le.append(tournament)
	ci = card['color_identity']
	return Card(na, li, im, ty, le, ci)


# https://scryfall.com/docs/api/cards/collection
# READ IT and figure out how to do mass collection.


def split_into(list_target, count):
	transform = []
	for i in range(0, len(list_target), count):
		chunk = list_target[i:i + count]
		transform.append(chunk)
	return transform


def request_list(names):
	output = []
	not_found = []
	for request in split_into(names, 75):
		query = convert_list(names)
		res = request_bulk(query)
		output.extend(res['data'])
		not_found.extend(res['not_found'])
		time.sleep(.1)  # API rule
	return output, not_found


def request_bulk(query):
	headers = {"Content-Type": "application/json"}  # Required by API
	return json.loads(post("https://api.scryfall.com/cards/collection", json=query, headers=headers).text)


def convert_list(card_names):
	dictionary = []
	for i in card_names:
		dictionary.append({"name": i})
	return {"identifiers": dictionary}


# print(input_to_decklist(z))
# print(input_to_decklist(z[:-1]))
# print(z[:-1])

if __name__ == '__main__':
	z = ["1 Plains", "2 Island", "1 Swamp", "3 Mountain", "70 Forest", "2 Wastes", "1 Brainstorm", "69 Ponder"]
	n = pipeline(z, "test", "standard")
	print(n)
