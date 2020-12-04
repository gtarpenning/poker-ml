from holdem_calc import parallel_holdem_calc as HCalc

all_cards = []
for face in ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']:
    for suit in ['s', 'h']:
        all_cards += [face + suit]

possible_hole_cards = []

for i in range(len(all_cards)):
    for j in range(i, len(all_cards)):
        pair = (all_cards[i], all_cards[j])
        if (all_cards[j], all_cards[i]) not in possible_hole_cards:
            possible_hole_cards += [pair]

# val = HCalc.calculate(None, True, 1, None, ["As", "Ah", "?", "?"], False)
# print(val)
print(HCalc.calculate(None, True, 1, None, ["8s", "7s", "Ad", "Ac"], False))
