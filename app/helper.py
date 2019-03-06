import random

def random_string(length=6):
	base_str = 'abcdefghijklnopqrstuvwxyz1234567890'
	return ''.join(random.choice(base_str) for i in range(length))