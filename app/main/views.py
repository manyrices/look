import os
from . import main
from flask import render_template ,redirect, url_for, request, current_app, jsonify
from ..helper import random_string, allowed_file, get_file_suffix_name
from werkzeug.utils import secure_filename

@main.route('/', methods=['GET','POST'])
def index():
	return render_template('index.html')

@main.route('/edit_avatar', methods=['GET','POST'])
def edit_avatar():
	return render_template('/edit_avatar.html')

@main.route('/upload_avatar', methods=['POST'])
def upload_avatar():
	file = request.files['avatar'].read()
	# cropper插件传输文件格式为二进制流，因此file文件类操作不能实现
	# if file.filename == '':
	# 	return redirect(url_for('main.edit_avatar'))
	# if file and allowed_file(file.filename):
	# 	filename = secure_filename(file.filename)
	# 	filename = random_string(32) + get_file_suffix_name(filename)
	# 	avatar = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
	# 	with open(avatar, 'wb+') as f:
	# 		f.write(data)
	# 	return jsonify(data=1)
	# return jsonify(data=0)
	if file:
		return jsonify(data=1)
	return jsonify(data=0)