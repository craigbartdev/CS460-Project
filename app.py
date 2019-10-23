#CS460
######################################
# Credits for original project template given by TAs
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# SQL scripts, schema design, and Flask functions for project
# done by Craig Bartholomew <cbartjr@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
#for image uploading
from werkzeug.utils import secure_filename
import os, base64
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('config.ini')

mysql = MySQL()
app = Flask(__name__)
app.secret_key = parser.get('some_stuff', 'key')  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = parser.get('some_stuff', 'password') #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
	return render_template('improved_register.html', supress='True')  

@app.route("/register/", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
                print email
		password=request.form.get('password')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		dob=request.form.get('birthday')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		print cursor.execute("INSERT INTO Users (email, password, firstname, lastname, dob, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(
			email, 
			password, 
			firstname, 
			lastname, 
			dob, 
			hometown, 
			gender)
		)
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=firstname, message='Account Created!', email=email)
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getEmailFromUserId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email  FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getPphotoFromUserId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT pphoto  FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getBioFromUserId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT bio  FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT Users.email, Users.user_id FROM Users, Friends WHERE Users.user_id != '{0}' AND Friends.user_id = '{0}' AND Friends.friend_id = Users.user_id".format(uid))
	return cursor.fetchall()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route("/browseall", methods=['GET', 'POST']) #browse all photos whether logged in or not
def show_photos():
	#uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		string = request.form.get('search', None)
		cursor = conn.cursor()
		cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption, Tags.tag FROM Pictures, Tags WHERE Tags.picture_id = Pictures.picture_id")
		data = []
		for item in cursor:
			if item[3] in string.split():
				data.append(item)
		return render_template('browse.html', data = data)
	else: 
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures")
		data = []
		for item in cursor:
			data.append(item)
		return render_template('browse.html', data = data)

@app.route("/browsemine", methods=['GET', 'POST']) #browse your own photos
@flask_login.login_required
def show_myphotos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		string = request.form.get('search', None)
		cursor = conn.cursor()
		cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption, Tags.tag FROM Pictures, Tags WHERE Tags.picture_id = Pictures.picture_id AND Pictures.user_id = '{0}'".format(uid))
		data = []
		for item in cursor:
			if item[3] in string.split():
				data.append(item)
		return render_template('browse.html', data = data, mine=True)
	else: 
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE Pictures.user_id = '{0}'".format(uid))
		data = []
		for item in cursor:
			data.append(item)
		return render_template('browse.html', data = data, mine=True)

@app.route('/profile') #show logged in user profile
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template(
		'hello.html', 
		email=flask_login.current_user.id, 
		message="Here's your profile",  
		profile=getPphotoFromUserId(uid),
		bio=getBioFromUserId(uid),
		friends=getUsersFriends(uid),
		albums=getUsersAlbums(uid)
	)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload/<aid>', methods=['GET', 'POST']) #upload regular photo
@flask_login.login_required
def upload_file(aid):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data,uid, caption, aid))
		conn.commit()
		return flask.redirect('album/' + str(aid))
	#The method is GET so we return a  HTML form to upload a photo.
	else:
		return render_template('upload.html', aid=aid)
#end photo uploading code 

@app.route('/profilepic', methods=['GET', 'POST']) #upload or render profile pic
@flask_login.login_required
def upload_profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("UPDATE Users SET pphoto = '{0}' WHERE user_id = '{1}'".format(photo_data,uid))
		conn.commit()
		return render_template('profilepic.html', profile=getPphotoFromUserId(uid))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('profilepic.html', profile=getPphotoFromUserId(uid))
	
@app.route('/bio', methods=['GET', 'POST']) #set bio
@flask_login.login_required
def update_profile():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		bio = request.form.get('bio', None)
		cursor = conn.cursor()
		cursor.execute("UPDATE Users SET bio = '{1}'  WHERE user_id = '{0}'".format(uid,bio))
		conn.commit()
		return render_template(
			'bio.html', 
			bio=getBioFromUserId(uid)
		)
	#The method is GET so we return an HTML form to enter bio
	else:
		return render_template(
			'bio.html', 
			bio=getBioFromUserId(uid)
		)

@app.route('/createalbum', methods=['GET', 'POST']) #create a photo album
@flask_login.login_required
def create_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album = request.form.get('album', None)
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (album_name, user_id, doa) VALUES ('{0}', '{1}', CURDATE())".format(album,uid))
		conn.commit()
		return flask.redirect('/profile')
	else:
		return render_template('createalbum.html')

def getPhotosByAlbumId(aid): #get photo album
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption, album_id FROM Pictures WHERE album_id = '{0}'".format(aid))
	return cursor.fetchall()

@app.route('/album/<int:aid>', methods=['GET']) #view photo album
@flask_login.login_required
def view_album(aid):
	return render_template('album.html', photos=getPhotosByAlbumId(aid), aid=aid)

@app.route("/addfriend", methods=['GET', 'POST']) #see friends
@flask_login.login_required
def show_list():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		string = request.form.get('users', None)
		cursor = conn.cursor()
		cursor.execute("SELECT Users.user_id, Users.email FROM Users, Friends WHERE Users.user_id != '{0}' AND Friends.user_id != '{0}'".format(uid))
		data = []
		for item in cursor:
			if areFriends(uid, item[0]) == False and item[1] == string:
				data.append(item)
		return render_template('friendlist.html', data = data)
	else: 
		cursor = conn.cursor()
		cursor.execute("SELECT Users.user_id, Users.email FROM Users, Friends WHERE Users.user_id != '{0}' AND Friends.user_id != '{0}'".format(uid))
		data = []
		for item in cursor:
			if areFriends(uid, item[0]) == False:
				data.append(item)
		return render_template('friendlist.html', data = data)

def areFriends(uid, fid): #check if friends with user
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id, friend_id  FROM Friends WHERE user_id = '{0}' AND friend_id = '{1}'".format(uid, fid)): 
		return True
	else:
		return False

@app.route("/added/<int:fid>", methods=['GET']) #add a friend
@flask_login.login_required
def show_added(fid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	if areFriends(uid, fid) == False:
		cursor.execute("INSERT INTO Friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, fid))
		conn.commit()
		return render_template('added.html', email=getEmailFromUserId(fid))
	else:
		return render_template('added.html', error="error", email=getEmailFromUserId(fid))

def getTagsFromPictureId(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT tag FROM Tags WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchall()

def getPhotoFromPictureId(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, caption, picture_id  FROM Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchone()

def getUserIdFromPictureId(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchone()[0]

def getCommentsFromPictureId(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT doc, comment, cid  FROM Comments WHERE Comments.picture_id = '{0}'".format(pid))
	return cursor.fetchall()

@app.route("/picture/<int:pid>", methods=['GET', 'POST']) #post picture and get comments for picture
def show_pic(pid):
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		logged = uid == getUserIdFromPictureId(pid)
		if logged:
			if request.method == 'POST':
				tag = request.form.get('tag', None)
				cursor = conn.cursor()
				cursor.execute("INSERT INTO Tags SET tag = '{0}', picture_id = '{1}'".format(tag,pid))
				conn.commit()
				return render_template(
					'picture.html',
					photo=getPhotoFromPictureId(pid),
					tags=getTagsFromPictureId(pid),
					comments=getCommentsFromPictureId(pid),
					logged=logged
				)
			else:
				return render_template(
					'picture.html',
					photo=getPhotoFromPictureId(pid),
					tags=getTagsFromPictureId(pid),
					comments=getCommentsFromPictureId(pid),
					logged=logged
				)
		else:
			if request.method == 'POST':
				comment = request.form.get('comment', None)
				cursor = conn.cursor()
				cursor.execute("INSERT INTO Comments (comment, user_id, picture_id, doc) VALUES ('{0}','{1}','{2}', CURDATE())".format(comment,uid,pid))
				conn.commit()
				return render_template(
					'picture.html',
					photo=getPhotoFromPictureId(pid),
					tags=getTagsFromPictureId(pid),
					comments=getCommentsFromPictureId(pid),
					logged=logged
				)
			else:
				return render_template(
					'picture.html',
					photo=getPhotoFromPictureId(pid),
					tags=getTagsFromPictureId(pid),
					comments=getCommentsFromPictureId(pid)
				)
	except:
		if request.method == 'POST':
			comment = request.form.get('comment', None)
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (comment, picture_id, doc) VALUES ('{0}','{1}', CURDATE())".format(comment,pid))
			conn.commit()
			return render_template(
				'picture.html',
				photo=getPhotoFromPictureId(pid),
				tags=getTagsFromPictureId(pid),
				comments=getCommentsFromPictureId(pid)
			)
		else:
			return render_template(
				'picture.html',
				photo=getPhotoFromPictureId(pid),
				tags=getTagsFromPictureId(pid),
				comments=getCommentsFromPictureId(pid)
			)

@app.route("/removephoto/<int:pid>", methods=['GET']) #delete a photo
@flask_login.login_required
def delete_pic(pid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{1}' AND user_id = '{0}'".format(uid, pid))
	conn.commit()
	return render_template('removed.html', photo=True)

@app.route("/removetag/<int:pid>/<string:tag>", methods=['GET']) #delete tag
@flask_login.login_required
def delete_tag(pid, tag):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Tags WHERE picture_id = '{0}' AND tag = '{1}'".format(pid, tag))
	conn.commit()
	return render_template('removed.html', tag=pid)

@app.route("/removefriend/<int:fid>", methods=['GET']) #delete friend
@flask_login.login_required
def delete_friend(fid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Friends WHERE user_id = '{0}' AND friend_id = '{1}'".format(uid, fid))
	conn.commit()
	return render_template('removed.html', friend=True)

#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
