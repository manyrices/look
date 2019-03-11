import random
from flask import current_app

def random_string(length=6):
	base_str = 'abcdefghijklnopqrstuvwxyz1234567890'
	return ''.join(random.choice(base_str) for i in range(length))

def get_file_suffix_name(filename):
	return '.' + filename.rsplit('.', 1)[1].lower()

def allowed_file(filename):
	return '.' in filename and \
	filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']