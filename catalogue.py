from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'Personal.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS Media_Item (
                media_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre_id INTEGER NOT NULL,
                release_year INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                media_type TEXT NOT NULL CHECK(media_type IN ('Book', 'CD', 'DVD', 'Vinyl', 'VideoGame')),
                creator_id INTEGER NOT NULL,
                location_id INTEGER, 
                FOREIGN KEY (genre_id) REFERENCES Genres (genre_id) ON DELETE SET NULL,
                FOREIGN KEY (location_id) REFERENCES Purchase_Locations (location_id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (creator_id) REFERENCES Media_Creators (creator_id) ON DELETE SET NULL
            );
                          
            CREATE TABLE IF NOT EXISTS Genres (
                genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                genre_name TEXT NOT NULL UNIQUE
            );
            
            CREATE TABLE IF NOT EXISTS Media_Creators (
                creator_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL CHECK(type IN ('Author', 'Director', 'Singer/Band', 'Designer'))
            );
                          
            CREATE TABLE IF NOT EXISTS Purchase_Locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                loc_name TEXT NOT NULL,
                address TEXT
            );

            CREATE TABLE IF NOT EXISTS DVDs (
                media_id INTEGER PRIMARY KEY,
                runtime INTEGER,
                studio TEXT,
                DVD_type TEXT NOT NULL,
                FOREIGN KEY (media_id) REFERENCES Media_Item (media_id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS Books (
                media_id INTEGER PRIMARY KEY,
                publisher TEXT,
                page_count INTEGER,
                description TEXT,
                FOREIGN KEY (media_id) REFERENCES Media_Item (media_id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS CDs (
                media_id INTEGER PRIMARY KEY,
                album_id INTEGER NOT NULL, 
                FOREIGN KEY (media_id) REFERENCES Media_Item (media_id) ON DELETE CASCADE,
                FOREIGN KEY (album_id) REFERENCES Albums (album_id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS Albums (
                album_id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_title TEXT NOT NULL,
                creator_id INTEGER NOT NULL,
                track_count INTEGER,
                runtime INTEGER,
                FOREIGN KEY (creator_id) REFERENCES Media_Creators (creator_id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS Vinyls (
                media_id INTEGER PRIMARY KEY,
                album_id INTEGER NOT NULL,
                disc_count INTEGER,
                FOREIGN KEY (media_id) REFERENCES Media_Item (media_id) ON DELETE CASCADE,
                FOREIGN KEY (album_id) REFERENCES Albums (album_id) ON DELETE CASCADE
            );
                          
            CREATE TABLE IF NOT EXISTS VideoGames (
                media_id INTEGER PRIMARY KEY,
                console TEXT NOT NULL,
                FOREIGN KEY (media_id) REFERENCES Media_Item (media_id) ON DELETE CASCADE
            );
        ''')
        
        # Insert predefined genres
        genres = [
            ('Action',),
            ('Adventure',),
            ('Comedy',),
            ('Drama',),
            ('Fantasy',),
            ('Horror',),
            ('Mystery',),
            ('Romance',),
            ('Sci-Fi',),
            ('Thriller',)
        ]
        cur.executemany('INSERT OR IGNORE INTO Genres (genre_name) VALUES (?)', genres)
        
        # Insert predefined creators
        creators = [
            ('Unknown Author', 'Author'),
            ('Unknown Director', 'Director'),
            ('Unknown Singer/Band', 'Singer/Band'),
            ('Unknown Designer', 'Designer')
        ]
        cur.executemany('INSERT OR IGNORE INTO Media_Creators (name, type) VALUES (?, ?)', creators)
        
        conn.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        # Check for special characters in username and password
        if not re.match("^[a-zA-Z0-9_]*$", username):
            flash('Username can only contain letters, numbers, and underscores.')
            return redirect(url_for('register'))
        
        if not re.match("^[a-zA-Z0-9_]*$", password):
            flash('Password can only contain letters, numbers, and underscores.')
            return redirect(url_for('register'))
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Users WHERE username = ?", (username,))
            user = cur.fetchone()
            
            if user:
                flash('Username already exists. Please choose a different username.')
                return redirect(url_for('register'))
            
            cur.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
            user = cur.fetchone()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]  # Store the username in the session
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials. Please try again.')
                return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        return render_template('home.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        publisher = request.form['publisher']
        page_count = request.form['page_count']
        description = request.form['description']
        author_name = request.form['author_input']
        location_name = request.form['location_input']
        user_id = session['user_id']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            
            # Check if the author already exists, otherwise insert a new one
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Author"', (author_name,))
            author = cur.fetchone()
            if author:
                author_id = author[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Author")', (author_name,))
                author_id = cur.lastrowid
            
            # Check if the location already exists, otherwise insert a new one
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid
            
            # Insert the book into Media_Item and Books tables
            cur.execute('''
                INSERT INTO Media_Item (title, genre_id, release_year, user_id, media_type, creator_id, location_id)
                VALUES (?, ?, ?, ?, 'Book', ?, ?)
            ''', (title, genre_id, release_year, user_id, author_id, location_id))
            media_id = cur.lastrowid
            cur.execute('''
                INSERT INTO Books (media_id, publisher, page_count, description)
                VALUES (?, ?, ?, ?)
            ''', (media_id, publisher, page_count, description))
            conn.commit()
        
        return redirect(url_for('view_books'))
    
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Author"')
        authors = [row[0] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row[0] for row in cur.fetchall()]
    
    return render_template('add_book.html', genres=genres, authors=authors, locations=locations)

@app.route('/view_books', methods=['GET', 'POST'])
def view_books():
    if 'user_id' in session:
        user_id = session['user_id']
        genre_filter = request.args.get('genre', None)
        sort_by = request.args.get('sort', None)

        query = '''
            SELECT Media_Item.media_id, Media_Item.title, Media_Creators.name, Books.page_count, 
                   Books.description, Books.publisher, Genres.genre_name
            FROM Media_Item
            JOIN Books ON Media_Item.media_id = Books.media_id
            JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
            JOIN Genres ON Media_Item.genre_id = Genres.genre_id
            WHERE Media_Item.user_id = ?
        '''
        params = [user_id]

        # Apply genre filter if selected
        if genre_filter:
            query += ' AND Genres.genre_name = ?'
            params.append(genre_filter)

        # Apply sorting if selected
        if sort_by == 'title':
            query += ' ORDER BY Media_Item.title ASC'
        elif sort_by == 'author':
            query += ' ORDER BY Media_Creators.name ASC'
        elif sort_by == 'page_count':
            query += ' ORDER BY Books.page_count ASC'

        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            books = cur.fetchall()

            # Fetch all genres for the filter dropdown
            cur.execute('SELECT genre_name FROM Genres')
            genres = [row[0] for row in cur.fetchall()]

        return render_template('view_books.html', books=books, genres=genres, selected_genre=genre_filter, sort_by=sort_by)
    else:
        return redirect(url_for('login'))

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' in session:
        user_id = session['user_id']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            # Ensure the book belongs to the logged-in user before deleting
            cur.execute('''
                DELETE FROM Media_Item
                WHERE media_id = ? AND user_id = ?
            ''', (book_id, user_id))
            conn.commit()
        flash('Book deleted successfully.')
        return redirect(url_for('view_books'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

