from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

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
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        
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
                return "Invalid credentials"
    
    return render_template('login.html')

@app.route('/')
def root():
    return redirect(url_for('login'))

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
        author_id = request.form['author_id']
        new_author = request.form['new_author']
        location_id = request.form['location_id']
        new_location_name = request.form['new_location_name']
        new_location_address = request.form['new_location_address']
        user_id = session['user_id']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            if new_author:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, ?)', (new_author, 'Author'))
                author_id = cur.lastrowid
            if new_location_name:
                cur.execute('INSERT INTO Purchase_Locations (loc_name, address) VALUES (?, ?)', (new_location_name, new_location_address))
                location_id = cur.lastrowid
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
        cur.execute('SELECT creator_id, name FROM Media_Creators WHERE type = "Author"')
        authors = cur.fetchall()
        cur.execute('SELECT location_id, loc_name FROM Purchase_Locations')
        locations = cur.fetchall()
    
    return render_template('add_book.html', genres=genres, authors=authors, locations=locations)

@app.route('/view_books')
def view_books():
    if 'user_id' in session:
        user_id = session['user_id']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT Media_Item.title,Media_Creators.name, Books.page_count, Books.description, Books.publisher
                FROM Media_Item
                JOIN Books ON Media_Item.media_id = Books.media_id
                JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
                WHERE Media_Item.user_id = ?
            ''', (user_id,))
            books = cur.fetchall()
        
        return render_template('view_books.html', books=books)
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

