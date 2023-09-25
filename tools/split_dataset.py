import json
import random

with open('A.json', 'r', encoding='utf-8') as f:
    original_data = json.load(f)

random.shuffle(original_data)
new_data = original_data[:1000]

with open('B.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f)