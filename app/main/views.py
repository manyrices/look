import os
from . import main
from .. import db
from flask import render_template ,redirect, url_for, request, current_app, jsonify
from ..helper import random_string
from flask_login import current_user, login_required

@main.route('/', methods=['GET','POST'])
def index():
	return render_template('index.html')

#头像编辑页面
@main.route('/edit_avatar', methods=['GET','POST'])
@login_required
def edit_avatar():
	user = current_user._get_current_object()
	return render_template('/edit_avatar.html', user=user)

#用户头像上传与编辑
@main.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
	file = request.files['avatar'].read()
	#获取当前真实登录用户
	user = current_user._get_current_object()
	if user is None:
		redirect(url_for('main.index'))
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
		filename = random_string(32) + '.jpg'
		avatar = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
		if user.avatar != 'default_avatar.jpg':
			os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], user.avatar))
		with open(avatar, 'wb+') as f:
			f.write(file)
		user.avatar = filename
		db.session.add(user)
		db.session.commit()
		return jsonify(data=1)
	return jsonify(data=0)