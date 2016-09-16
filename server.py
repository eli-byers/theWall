from flask import Flask, request, redirect, render_template, session, flash, escape
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'DojoNinjaSoSkeaky'
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app,'theWall')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

# ==============================================================
#                           RENDER
# ==============================================================
@app.route('/')
def index():
    if 'user_id' in session and 'name' in session:
        return redirect('/wall')

    return render_template('index.html')

@app.route('/wall')
def wall():
    # validate session
    if 'user_id' in session and 'name' in session:

        # get messages
        queryStr = 'SELECT messages.id, text, messages.created_at, users.id as author_id, users.name as author FROM messages JOIN users ON messages.user_id = users.id ORDER BY created_at DESC';
        messages = mysql.query_db(queryStr)

        # get comments
        queryStr = 'SELECT comments.id, message_id, text, comments.created_at, users.id as author_id, users.name as author FROM comments JOIN users ON comments.user_id = users.id';
        comments = mysql.query_db(queryStr)

        # render the wall
        return render_template('wall.html', messages=messages, comments=comments)

    return redirect ('/')

# ==============================================================
#                     Messages & Comments
# ==============================================================

@app.route('/message', methods=['post'])
def new_message():
    # because it's shorter
    post = request.form
    print post

    # test for post data
    if 'message' in post:
        queryStr = 'INSERT INTO messages (text, user_id, created_at, updated_at) VALUES (:text, :user_id, NOW(), NOW())'
        data = {'text': post['message'], 'user_id': session['user_id']}
        mysql.query_db(queryStr, data)

    return redirect('/wall')

@app.route('/message/delete/<id>')
def delete_message(id):
    # validate that the message was made by the current in user
    queryStr = 'SELECT * FROM messages WHERE id = :id AND user_id = :user_id'
    data = {'id': id, 'user_id': session['user_id']}
    messages = mysql.query_db(queryStr, data)

    if messages:
        data = {'id': id}

        queryStr = 'DELETE FROM comments WHERE message_id = :id'
        mysql.query_db(queryStr, data)
        queryStr = 'DELETE FROM messages WHERE id = :id'
        mysql.query_db(queryStr, data)

    return redirect('/wall')

@app.route('/comment', methods=['post'])
def new_comment():
    # because it's shorter
    post = request.form
    print post

    # test for post data
    if 'text' in post and 'message_id' in post:
        queryStr = 'INSERT INTO comments (text, message_id, user_id, created_at, updated_at) VALUES (:text, :message_id, :user_id, NOW(), NOW())'
        print queryStr
        data = {'text': post['text'], 'message_id': post['message_id'], 'user_id': session['user_id']}
        mysql.query_db(queryStr, data)

    return redirect('/wall')

@app.route('/comment/delete/<id>')
def delete_comment(id):
    # validate that the comment was made by the current in user
    queryStr = 'SELECT * FROM comments WHERE id = :id AND user_id = :user_id'
    data = {'id': id, 'user_id': session['user_id']}
    comments = mysql.query_db(queryStr, data)

    if comments:
        queryStr = 'DELETE FROM comments WHERE id = :id'
        data = {'id': id}
        mysql.query_db(queryStr, data)

    return redirect('/wall')


# @app.route('/message/edit/<id>')
# def get_message():
#     # pull out messageId
#     messageId = request.args.get('id')
#
#     # get message
#     queryStr = 'SELECT * FROM messages WHERE id = :id AND user_id = :user_id'
#     data = {'id': messageId, 'user_id': session['user_id']}
#     message = mysql.query_db(queryStr, data)
#
#     # render if message was made by logged in user render edit page
#     if message: return render_template('edit_message', message=message)
#
#     # if someone elses message redirect to wall
#     else: return redirect('/wall')
#
# @app.route('/comment/edit/<id>')
# def get_comment():
#     # pull out commentId
#     commentId = request.args.get('id')
#
#     # get comment
#     queryStr = 'SELECT * FROM comments WHERE id = :id AND user_id = :user_id'
#     data = {'id': commentId, 'user_id': session['user_id']}
#     comment = mysql.query_db(queryStr, data)
#
#     # render if comment was made by logged in user
#     if comment: return render_template('edit_comment', comment=comment)
#
#     # if someone elses message redirect to wall
#     else: return redirect('/wall')

# ==============================================================
#                       LOGIN & REGISTRATION
# ==============================================================

@app.route('/users/login', methods=['POST'])
def login():
    # because it's shorter
    post = request.form
    print post

    # test for post data
    if 'email' in post and 'password' in post:

        # escape inputs
        email = escape(post['email']).lower()
        password = escape(post['password'])

        # test for valid inputs
        if email and password:

            # see if a user with 'email' exists
            queryStr = 'SELECT * FROM users WHERE email = :email'
            data = {'email': email}
            user = mysql.query_db(queryStr, data)

            # if there is a user with 'email'
            if user:

                # test password
                if bcrypt.check_password_hash(user[0]['password'], password):

                    # set session and go to the wall
                    session['user_id'] = int(user[0]['id'])
                    session['name'] = user[0]['name']
                    return redirect('/wall')


            flash("Email and password do not match", 'lg_email')

        # set errors for empty inputs
        else:
            if not post['email']: flash("Email cannot be blank", 'lg_email')
            if not post['password']: flash("Password cannot be blank", 'lg_password')

    # if it failed reload the login page
    return redirect('/')

@app.route('/users', methods=['POST'])
def create():
    # because it's shorter
    post = request.form

    # test for post data
    if 'name' in post and 'email' in post and 'password' in post and 'passwordConfirm' in post:

        # escape inputs
        name = escape(post['name'])
        email = escape(post['email'])
        password = escape(post['password'])
        passwordConfirm = escape(post['passwordConfirm'])

        err = False

        # validate inputs
        if not name:
            err = True
            flash("Name cannot be blank", "name")
        if not email:
            err = True
            flash("Email cannot be blank", "email")
        elif not EMAIL_REGEX.match(email):
            err = True
            flash("Invalid email address", "email")
        if not password:
            err = True
            flash("Password cannot be blank", "password")
        if not passwordConfirm:
            err = True
            flash("Password Confirmation cannot be blank", "passwordConfirm")
        if password and passwordConfirm and password != passwordConfirm:
            err = True
            flash("Passwords do not match", "password")

        # if there were no errors
        if not err:

            # encrypt password
            encrypted_password = bcrypt.generate_password_hash(password)

            # insert user
            queryStr = "INSERT INTO Users (name, email, password, created_at, updated_at) VALUES (:name, :email, :password, NOW(), NOW())"
            data = {'name': name.lower(),'email': email, 'password': encrypted_password}
            user_id = mysql.query_db(queryStr, data)

            # set session
            session['user_id'] = int(user_id)
            session['name'] = name
            return redirect('/wall')

    # if it failed reload the login page
    return redirect('/')

@app.route('/logout')
def logout():
    # clear our session variables
    session.pop('user_id', None)
    session.pop('name', None)

    # redirect to login
    return redirect('/')


# end of file
app.run(debug=True)
