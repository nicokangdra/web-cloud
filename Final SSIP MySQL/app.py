import os
import hashlib
from flask import (
    Flask, render_template, request, redirect, url_for,session,flash,send_from_directory
)
from db import db_connection

app = Flask(__name__)
app.secret_key = 'THISISMYSECRETKEY'

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = 900 #set session timeout

# routing for register
@app.route('/register', methods=['GET', 'POST'])
def registerpage():
    # if request method is post go to this function
    if request.method == "POST" :
        username = request.form['Rusername']
        password = hashlib.md5(request.form['Rpassword'].encode()).hexdigest() # hash the password
        name = request.form['Rname']
        type = request.form['type']
        passwordcon = hashlib.md5(request.form['passwordcon'].encode()).hexdigest()

        conn = db_connection()
        curs = conn.cursor()
        curs.execute("SELECT username FROM users WHERE username = '%s'" %username)
        check = curs.fetchone()
        curs.close()

        if not check :
            if password == passwordcon :
                cur = conn.cursor()
                sql = """INSERT INTO users (username, password, name, type) VALUES('%s','%s','%s','%s')"""%(username,password,name,type)
                cur.execute(sql)
                conn.commit()
                cur.close()
                conn.close()
                return redirect('/login')
            else :
                flash("Password must match")
        else:
            flash("Username already taken")

    # if there is no request method then return the code below
    return render_template("register.html")

# routing for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # function to show and process login page
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()

        conn = db_connection()
        cur = conn.cursor()
        sql = """
            SELECT id, username, type, name
            FROM users
            WHERE username = '%s' AND password = '%s'
        """ % (username, password)
        cur.execute(sql)
        user = cur.fetchone()

        error = ''
        if user is None:
            error = 'Wrong credentials. No user found'
        else:
            # store to the session
            session.clear()
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['type'] = user[2]
            session['name'] = user[3]
            return redirect(url_for('index'))

        flash(error)
        cur.close()
        conn.close()

    return render_template('login.html')

# routing for logout
@app.route('/logout')
def logout():
    # function to do logout 
    session.clear()  # clear all sessions
    return redirect(url_for('login'))

# main pages
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search = request.form['livebox']
        boxx = search.lower() + "%"
        db = db_connection()
        cur = db.cursor()
        sql = """ SELECT name, id, LOWER(name) FROM books WHERE LOWER(name) LIKE '%s' """%boxx
        cur.execute(sql)
        res = cur.fetchall()
        cur.close()
        db.close()
        return render_template('index.html',res=res)
    return render_template('index.html')

# list all genre
@app.route('/categories', methods=['GET'])
def list_categories():
    categories = get_all_categories()
    return render_template('category/index.html', categories=categories)

# create new genre
@app.route('/category/create', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        name = request.form['name']
        data = {
            'name': name,
        }
        save_category(data)
        return redirect(url_for('list_categories'))

    return render_template('category/create.html')

# edit genre
@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = get_category_by_id(category_id)

    if request.method == 'POST':
        name = request.form['name']
        data = {
            'id': category_id,
            'name': name,
        }
        save_category(data)
        return redirect(url_for('list_categories'))

    return render_template('category/edit.html', category=category)

# delete the genre
@app.route('/category/delete/<int:category_id>', methods=['GET', 'POST'])
def delete_category(category_id):
    category = get_category_by_id(category_id)

    if request.method == 'POST':
        remove_category_by_id(category_id)
        return redirect(url_for('list_categories'))

    return render_template('category/delete.html', category=category)

# view the genre
@app.route('/category/view/<int:category_id>', methods=['GET', 'POST'])
def view_category(category_id):
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT bk.id, bk.name, bk.category_id, ct.name
        FROM books bk
        JOIN categories ct ON bk.category_id = ct.id
        WHERE category_id = %d
        ORDER BY bk.name
    """%int(category_id)
    cur.execute(sql)
    category = cur.fetchall()
    cur.close()
    db.close()
    return render_template('category/view.html',category = category)

# function to get all categories
def get_all_categories():
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT id, name
        FROM categories
        ORDER BY name
    """
    cur.execute(sql)
    categories = cur.fetchall()
    cur.close()
    db.close()
    return categories

# function to get categories based on ID
def get_category_by_id(category_id):
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT id, name
        FROM categories
        WHERE id = %d
    """ % (int(category_id))
    cur.execute(sql)
    category = cur.fetchone()
    cur.close()
    db.close()
    return category

# save the category/genre
def save_category(data):
    if data:
        name = data.get('name')

        sql = """
            INSERT INTO categories (name) VALUES ('%s')
        """ % (name)

        if data.get('id'):  # if there's ID, then UPDATE
            category_id = data.get('id')
            sql = """
                UPDATE categories SET name = '%s' WHERE id = %d
            """ % (name, category_id)

        db = db_connection()
        cur = db.cursor()
        cur.execute(sql)
        db.commit()
        cur.close()
        db.close()

# delete category by ID
def remove_category_by_id(category_id):
    db = db_connection()
    cur = db.cursor()
    sql = """
        DELETE FROM categories WHERE id = %d
    """ % (int(category_id))
    sqls = """
        DELETE FROM books WHERE category_id = %d
    """ % (int(category_id))
    cur.execute(sqls)
    cur.execute(sql)
    db.commit()
    cur.close()
    db.close()

# routing for book
@app.route('/books')
def list_books():
    books = get_all_books()
    return render_template('book/index.html', books=books)

# declare upload folder for file upload
app.config['UPLOAD_FOLDER'] = 'files'
@app.route('/book/create', methods=['GET', 'POST'])
def create_book():
    categories = get_all_categories()

    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category_id']
        desc = request.form['body']
        files = request.files['file']
        # save the file
        files.save(os.path.join(app.config['UPLOAD_FOLDER'], files.filename))
        data = {
            'name': name,
            'category_id': int(category_id),
            'desc' : desc,
            'file' : files.filename,
        }
        save_book(data)
        return redirect(url_for('list_books'))

    return render_template('book/create.html', categories=categories)

# edit book
@app.route('/book/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = get_book_by_id(book_id)
    categories = get_all_categories()

    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category_id']
        desc = request.form['body']
        files = request.files['file']
        filesx = book[4]
        if files :
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filesx))
            filesx = files.filename
            files.save(os.path.join(app.config['UPLOAD_FOLDER'], files.filename))
        data = {
            'id': book_id,
            'name': name,
            'category_id': int(category_id),
            'desc' : desc,
            'file' : filesx,
        }
        save_book(data)
        return redirect(url_for('list_books'))

    return render_template('book/edit.html', book=book, categories=categories)

# delete book
@app.route('/book/delete/<int:book_id>', methods=['GET', 'POST'])
def delete_book(book_id):
    book = get_book_by_id(book_id)

    if request.method == 'POST':
        remove_book_by_id(book_id)
        files = book[4]
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], files))
        return redirect(url_for('list_books'))

    return render_template('book/delete.html', book=book)

# view book preview
@app.route('/book/view/<int:book_id>')
def view_book(book_id):
    book = get_book_by_id(book_id)
    return render_template('book/view.html', book=book)

# view pdf
@app.route('/book/view/detail/<int:book_id>')
def view_book_detail(book_id):
    db = db_connection()
    cur = db.cursor()
    sql = """SELECT file FROM books WHERE id = %s""" %book_id
    cur.execute(sql)
    books = cur.fetchone()
    cur.close()
    db.close()
    return send_from_directory(app.config['UPLOAD_FOLDER'],books[0], as_attachment=False)

# function to get all of the books
def get_all_books():

    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT book.id, book.name, category.name
        FROM books book
        JOIN categories category ON category.id = book.category_id
        ORDER BY book.name
    """
    cur.execute(sql)
    books = cur.fetchall()
    cur.close()
    db.close()
    return books

# get book based by ID
def get_book_by_id(book_id):

    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT book.id, book.name, book.category_id, book.description, book.file
        FROM books book
        WHERE book.id = %d
    """ % (int(book_id))
    cur.execute(sql)
    book = cur.fetchone()
    cur.close()
    db.close()
    return book

# save the book
def save_book(data):
    if data:
        name = data.get('name')
        category_id = data.get('category_id')
        desc = data.get('desc')
        file = data.get('file')

        sql = """
            INSERT INTO books (name, category_id, description, file) VALUES ('%s', %d,'%s','%s')
        """ % (name, category_id,desc,file)

        if data.get('id'):  # if there is id in the data dict, UPDATE
            name = data.get('name')
            category_id = data.get('category_id')
            desc = data.get('desc')
            file = data.get('file')
            book_id = data.get('id')
            sql = """
                UPDATE books SET name = '%s', category_id = %d, description = '%s', file = '%s' WHERE id = %d
            """ % (name, category_id,desc, file, book_id)

        db = db_connection()
        cur = db.cursor()
        cur.execute(sql)
        db.commit()
        cur.close()
        db.close()

# remove the book
def remove_book_by_id(book_id):
    db = db_connection()
    cur = db.cursor()
    sql = """
        DELETE FROM books WHERE id = %d
    """ % (int(book_id))
    cur.execute(sql)
    db.commit()
    cur.close()
    db.close()

# user page
@app.route('/user')
def user_manage():
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT id, username, type, name FROM users WHERE id = %d
    """ %int(session['user_id'])
    cur.execute(sql)
    users = cur.fetchone()
    cur.close()
    db.close()
    return render_template('users/index.html',users=users)

# change password
@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT id, username, type, password FROM users WHERE id = %d
    """ %int(user_id)
    cur.execute(sql)
    users = cur.fetchone()
    cur.close()

    if request.method == "POST" :
        password = hashlib.md5(request.form['Rpassword'].encode()).hexdigest() 
        passwordcon = hashlib.md5(request.form['passwordcon'].encode()).hexdigest()
        pwnow = hashlib.md5(request.form['pwnow'].encode()).hexdigest()

        if pwnow == users[3] :
            if password == passwordcon :
                curs = db.cursor()
                sqls = """
                    UPDATE users SET password = '%s' WHERE id = %d
                """ %(password,users[0])
                curs.execute(sqls)
                db.commit()
                curs.close()
                db.close()
                return redirect('/')
            else :
                flash("Password must match")
        else :
            flash("Current Password is Wrong")
        

    return render_template('users/edit.html',users=users)

# delete user
@app.route('/user/delete/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT id, username, type FROM users WHERE id = %d
    """ %int(user_id)
    cur.execute(sql)
    users = cur.fetchone()
    cur.close()

    if request.method == "POST":
        curs = db.cursor()
        sqls = """
            DELETE FROM users WHERE id = %d
        """ % users[0]
        curs.execute(sqls)
        db.commit()
        curs.close()
        db.close()
        session.clear()
        return redirect('/')
    return render_template('users/delete.html',users=users)

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")
