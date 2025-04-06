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
                media_type TEXT NOT NULL CHECK(media_type IN ('Book', 'CD', 'DVD', 'Vinyl', 'VideoGame', 'Music')),
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

            CREATE TABLE IF NOT EXISTS Tracks (
                track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id INTEGER NOT NULL,
                track_name TEXT NOT NULL,
                FOREIGN KEY (album_id) REFERENCES Albums (album_id) ON DELETE CASCADE
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
            ('Thriller',),
            # Music-specific genres
            ('Pop',),
            ('Rock',),
            ('Jazz',),
            ('Classical',),
            ('Hip-Hop',),
            ('Electronic',),
            ('Country',),
            ('Blues',),
            ('Reggae',),
            ('Soul',),
            ('Metal',),
            ('Folk',),
            ('R&B',),
            ('Punk',)
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

@app.route('/add_dvd', methods=['GET', 'POST'])
def add_dvd():
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        runtime = request.form['runtime']
        studio = request.form['studio']
        dvd_type = request.form['dvd_type']
        director_name = request.form['director_input']
        location_name = request.form['location_input']
        user_id = session['user_id']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            
            # Check if the director already exists, otherwise insert a new one
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Director"', (director_name,))
            director = cur.fetchone()
            if director:
                director_id = director[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Director")', (director_name,))
                director_id = cur.lastrowid
            
            # Check if the location already exists, otherwise insert a new one
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid
            
            # Insert the DVD into Media_Item and DVDs tables
            cur.execute('''
                INSERT INTO Media_Item (title, genre_id, release_year, user_id, media_type, creator_id, location_id)
                VALUES (?, ?, ?, ?, 'DVD', ?, ?)
            ''', (title, genre_id, release_year, user_id, director_id, location_id))
            media_id = cur.lastrowid
            cur.execute('''
                INSERT INTO DVDs (media_id, runtime, studio, DVD_type)
                VALUES (?, ?, ?, ?)
            ''', (media_id, runtime, studio, dvd_type))
            conn.commit()
        
        return redirect(url_for('view_dvds'))
    
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Director"')
        directors = [row[0] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row[0] for row in cur.fetchall()]
    
    return render_template('add_dvd.html', genres=genres, directors=directors, locations=locations)

@app.route('/add_videogame', methods=['GET', 'POST'])
def add_videogame():
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        console = request.form['console']
        developer_name = request.form['developer_input']
        location_name = request.form['location_input']
        user_id = session['user_id']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            
            # Check if the developer already exists, otherwise insert a new one
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Designer"', (developer_name,))
            developer = cur.fetchone()
            if developer:
                developer_id = developer[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Designer")', (developer_name,))
                developer_id = cur.lastrowid
            
            # Check if the location already exists, otherwise insert a new one
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid
            
            # Insert the video game into Media_Item and VideoGames tables
            cur.execute('''
                INSERT INTO Media_Item (title, genre_id, release_year, user_id, media_type, creator_id, location_id)
                VALUES (?, ?, ?, ?, 'VideoGame', ?, ?)
            ''', (title, genre_id, release_year, user_id, developer_id, location_id))
            media_id = cur.lastrowid
            cur.execute('''
                INSERT INTO VideoGames (media_id, console)
                VALUES (?, ?)
            ''', (media_id, console))
            conn.commit()
        
        return redirect(url_for('view_videogames'))
    
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Designer"')
        developers = [row[0] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row[0] for row in cur.fetchall()]
    
    return render_template('add_videogame.html', genres=genres, developers=developers, locations=locations)

@app.route('/add_music', methods=['GET', 'POST'])
def add_music():
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        album_title = request.form['album_title']
        track_count = request.form['track_count']
        runtime = request.form['runtime']
        track_names = request.form.getlist('track_names')
        creator_name = request.form['creator_input']
        location_name = request.form['location_input']

        is_cd = 'is_cd' in request.form
        is_vinyl = 'is_vinyl' in request.form
        disc_count = request.form.get('disc_count') if is_vinyl else None

        # Determine media_type value
        if is_cd:
            media_type = 'CD'
        elif is_vinyl:
            media_type = 'Vinyl'

        user_id = session['user_id']

        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()

            # Creator lookup/insert
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Singer/Band"', (creator_name,))
            creator = cur.fetchone()
            if creator:
                creator_id = creator[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Singer/Band")', (creator_name,))
                creator_id = cur.lastrowid

            # Location lookup/insert
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid

            # Insert album
            cur.execute('''
                INSERT INTO Albums (album_title, creator_id, track_count, runtime)
                VALUES (?, ?, ?, ?)
            ''', (album_title, creator_id, track_count, runtime))
            album_id = cur.lastrowid

            # Insert into Media_Item
            cur.execute('''
                INSERT INTO Media_Item (title, genre_id, release_year, user_id, media_type, creator_id, location_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, genre_id, release_year, user_id, media_type, creator_id, location_id))
            media_id = cur.lastrowid

            # Insert into CDs or Vinyls
            if is_cd:
                cur.execute('''
                    INSERT INTO CDs (media_id, album_id)
                    VALUES (?, ?)
                ''', (media_id, album_id))
            elif is_vinyl:
                cur.execute('''
                    INSERT INTO Vinyls (media_id, album_id, disc_count)
                    VALUES (?, ?, ?)
                ''', (media_id, album_id, disc_count))

            # Insert tracks
            for track_name in track_names:
                if track_name.strip():
                    cur.execute('''
                        INSERT INTO Tracks (album_id, track_name)
                        VALUES (?, ?)
                    ''', (album_id, track_name.strip()))

            conn.commit()

        flash('Music item added successfully.')
        return redirect(url_for('home'))

    # GET method: load form
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row[0] for row in cur.fetchall()]

    return render_template('add_music.html', genres=genres, locations=locations)


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

@app.route('/view_dvds', methods=['GET', 'POST'])
def view_dvds():
    if 'user_id' in session:
        user_id = session['user_id']
        genre_filter = request.args.get('genre', None)
        sort_by = request.args.get('sort', None)

        query = '''
            SELECT Media_Item.media_id, Media_Item.title, Genres.genre_name AS genre, Media_Item.release_year,
                   DVDs.runtime, DVDs.studio, DVDs.DVD_type, Media_Creators.name AS director
            FROM Media_Item
            JOIN DVDs ON Media_Item.media_id = DVDs.media_id
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
        elif sort_by == 'director':
            query += ' ORDER BY Media_Creators.name ASC'
        elif sort_by == 'runtime':
            query += ' ORDER BY DVDs.runtime ASC'

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # Enable dictionary-like access
            cur = conn.cursor()
            cur.execute(query, params)
            dvds = cur.fetchall()

            # Fetch all genres for the filter dropdown
            cur.execute('SELECT genre_name FROM Genres')
            genres = [row['genre_name'] for row in cur.fetchall()]

        return render_template('view_dvds.html', dvds=dvds, genres=genres, selected_genre=genre_filter, sort_by=sort_by)
    else:
        return redirect(url_for('login'))

@app.route('/view_videogames', methods=['GET', 'POST'])
def view_videogames():
    if 'user_id' in session:
        user_id = session['user_id']
        genre_filter = request.args.get('genre', None)
        sort_by = request.args.get('sort', None)

        query = '''
            SELECT Media_Item.media_id, Media_Item.title, Genres.genre_name AS genre, Media_Item.release_year,
                   VideoGames.console, Media_Creators.name AS developer
            FROM Media_Item
            JOIN VideoGames ON Media_Item.media_id = VideoGames.media_id
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
        elif sort_by == 'developer':
            query += ' ORDER BY Media_Creators.name ASC'
        elif sort_by == 'console':
            query += ' ORDER BY VideoGames.console ASC'

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # Enable dictionary-like access
            cur = conn.cursor()
            cur.execute(query, params)
            videogames = cur.fetchall()

            # Fetch all genres for the filter dropdown
            cur.execute('SELECT genre_name FROM Genres')
            genres = [row['genre_name'] for row in cur.fetchall()]

        return render_template('view_videogames.html', videogames=videogames, genres=genres, selected_genre=genre_filter, sort_by=sort_by)
    else:
        return redirect(url_for('login'))

@app.route('/view_music', methods=['GET', 'POST'])
def view_music():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    genre_filter = request.args.get('genre', None)
    sort_by = request.args.get('sort', 'title')  # default sort
    media_format = request.args.get('media_format', None)
    search_creator = request.args.get('search_creator', '').strip()
    search_track = request.args.get('search_track', '').strip()

    # Allowed sort options mapping
    sort_options = {
    'title': 'Media_Item.title',
    'creator': 'Media_Creators.name',
    'album_title': 'Albums.album_title',
    'year': 'Media_Item.release_year',
    'genre': 'Genres.genre_name',
    'runtime': 'Albums.runtime'
    }

    sort_clause = sort_options.get(sort_by, 'Media_Item.title')  # fallback to title

    # Base query
    query = '''
        SELECT Media_Item.media_id, Media_Item.title, Media_Item.media_type,
               Albums.album_title, Albums.track_count, Albums.runtime,
               Media_Creators.name AS creator, Genres.genre_name AS genre, Media_Item.release_year,
               GROUP_CONCAT(Tracks.track_name, ', ') AS track_names
        FROM Media_Item
        JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
        JOIN Genres ON Media_Item.genre_id = Genres.genre_id
        LEFT JOIN CDs ON Media_Item.media_id = CDs.media_id
        LEFT JOIN Vinyls ON Media_Item.media_id = Vinyls.media_id
        LEFT JOIN Albums ON Albums.album_id = CDs.album_id OR Albums.album_id = Vinyls.album_id
        LEFT JOIN Tracks ON Albums.album_id = Tracks.album_id
        WHERE Media_Item.user_id = ?
          AND Media_Item.media_type IN ('CD', 'Vinyl')
    '''
    params = [user_id]

    # Filters
    if genre_filter:
        query += ' AND Genres.genre_name = ?'
        params.append(genre_filter)

    if media_format == 'CD':
        query += ' AND Media_Item.media_type = "CD"'
    elif media_format == 'Vinyl':
        query += ' AND Media_Item.media_type = "Vinyl"'

    if search_creator:
        query += ' AND Media_Creators.name LIKE ?'
        params.append(f"%{search_creator}%")

    if search_track:
        query += '''
            AND EXISTS (
                SELECT 1 FROM Tracks t
                WHERE t.album_id = Albums.album_id AND t.track_name LIKE ?
            )
        '''
        params.append(f"%{search_track}%")

    # ✅ Grouping must come before ordering
    query += ' GROUP BY Media_Item.media_id'
    query += f' ORDER BY {sort_clause} COLLATE NOCASE'

    # Execute
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        music_items = cur.fetchall()

        # Load genres for dropdown
        cur.execute('SELECT genre_name FROM Genres')
        genres = [row['genre_name'] for row in cur.fetchall()]

    return render_template(
        'view_music.html',
        music_items=music_items,
        genres=genres,
        selected_genre=genre_filter,
        sort_by=sort_by,
        selected_format=media_format,
        search_creator=search_creator,
        search_track=search_track
    )

@app.route('/view_all', methods=['GET'])
def view_all():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'media_type')  # Default sort by media_type
    filter_type = request.args.get('type', '')  # Filter by media_type

    # Allowed sort options
    sort_options = {
        'title': 'Media_Item.title',
        'media_type': 'Media_Item.media_type',
        'release_year': 'Media_Item.release_year'
    }
    sort_clause = sort_options.get(sort_by, 'Media_Item.media_type')  # Fallback to media_type

    # Base query
    query = '''
        SELECT Media_Item.media_id, Media_Item.title, Media_Item.media_type, Media_Item.release_year, 
               Genres.genre_name, Media_Creators.name AS creator
        FROM Media_Item
        JOIN Genres ON Media_Item.genre_id = Genres.genre_id
        JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
        WHERE Media_Item.user_id = ?
    '''
    params = [user_id]

    # Apply search filter
    if search_query:
        query += ' AND Media_Item.title LIKE ?'
        params.append(f"%{search_query}%")

    # Apply type filter
    if filter_type:
        query += ' AND Media_Item.media_type = ?'
        params.append(filter_type)

    # Apply sorting
    query += f' ORDER BY {sort_clause} COLLATE NOCASE'

    # Execute query
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        items = cur.fetchall()

    return render_template('view_all.html', items=items, search_query=search_query, sort_by=sort_by, filter_type=filter_type)

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

@app.route('/delete_dvd/<int:dvd_id>', methods=['POST'])
def delete_dvd(dvd_id):
    if 'user_id' in session:
        user_id = session['user_id']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            # Ensure the DVD belongs to the logged-in user before deleting
            cur.execute('''
                DELETE FROM Media_Item
                WHERE media_id = ? AND user_id = ?
            ''', (dvd_id, user_id))
            conn.commit()
        flash('DVD deleted successfully.')
        return redirect(url_for('view_dvds'))
    else:
        return redirect(url_for('login'))

@app.route('/delete_videogame/<int:videogame_id>', methods=['POST'])
def delete_videogame(videogame_id):
    if 'user_id' in session:
        user_id = session['user_id']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            # Ensure the video game belongs to the logged-in user before deleting
            cur.execute('''
                DELETE FROM Media_Item
                WHERE media_id = ? AND user_id = ?
            ''', (videogame_id, user_id))
            conn.commit()
        flash('Video game deleted successfully.')
        return redirect(url_for('view_videogames'))
    else:
        return redirect(url_for('login'))
    

@app.route('/delete_music/<int:media_id>', methods=['POST'])
def delete_music(media_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM Media_Item WHERE media_id = ? AND user_id = ?', (media_id, user_id))
        conn.commit()

    flash('Music item deleted.')
    return redirect(url_for('view_music'))

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        # Ensure the book belongs to the logged-in user
        cur.execute('''
            SELECT Media_Item.title, Media_Item.genre_id, Media_Item.release_year, 
                   Books.publisher, Books.page_count, Books.description, 
                   Media_Creators.name, Purchase_Locations.loc_name
            FROM Media_Item
            JOIN Books ON Media_Item.media_id = Books.media_id
            JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
            LEFT JOIN Purchase_Locations ON Media_Item.location_id = Purchase_Locations.location_id
            WHERE Media_Item.media_id = ? AND Media_Item.user_id = ?
        ''', (book_id, user_id))
        book = cur.fetchone()
        
        if not book:
            flash('Book not found or you do not have permission to edit it.')
            return redirect(url_for('view_books'))
        
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Author"')
        authors = [row[0] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row[0] for row in cur.fetchall()]
    
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        publisher = request.form['publisher']
        page_count = request.form['page_count']
        description = request.form['description']
        author_name = request.form['author_input']
        location_name = request.form['location_input']
        
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
            
            # Update the Media_Item and Books tables
            cur.execute('''
                UPDATE Media_Item
                SET title = ?, genre_id = ?, release_year = ?, creator_id = ?, location_id = ?
                WHERE media_id = ? AND user_id = ?
            ''', (title, genre_id, release_year, author_id, location_id, book_id, user_id))
            cur.execute('''
                UPDATE Books
                SET publisher = ?, page_count = ?, description = ?
                WHERE media_id = ?
            ''', (publisher, page_count, description, book_id))
            conn.commit()
        
        flash('Book updated successfully.')
        return redirect(url_for('view_books'))
    
    return render_template('edit_book.html', book=book, genres=genres, authors=authors, locations=locations)

@app.route('/edit_dvd/<int:dvd_id>', methods=['GET', 'POST'])
def edit_dvd(dvd_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cur = conn.cursor()
        # Ensure the DVD belongs to the logged-in user
        cur.execute('''
            SELECT Media_Item.media_id, Media_Item.title, Media_Item.genre_id, Media_Item.release_year, 
                   DVDs.runtime, DVDs.studio, DVDs.DVD_type, 
                   Media_Creators.name AS director, Purchase_Locations.loc_name
            FROM Media_Item
            JOIN DVDs ON Media_Item.media_id = DVDs.media_id
            JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
            LEFT JOIN Purchase_Locations ON Media_Item.location_id = Purchase_Locations.location_id
            WHERE Media_Item.media_id = ? AND Media_Item.user_id = ?
        ''', (dvd_id, user_id))
        dvd = cur.fetchone()
        
        if not dvd:
            flash('DVD not found or you do not have permission to edit it.')
            return redirect(url_for('view_dvds'))
        
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Director"')
        directors = [row['name'] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row['loc_name'] for row in cur.fetchall()]
    
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        runtime = request.form['runtime']
        studio = request.form['studio']
        dvd_type = request.form['dvd_type']
        director_name = request.form['director_input']
        location_name = request.form['location_input']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            
            # Check if the director already exists, otherwise insert a new one
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Director"', (director_name,))
            director = cur.fetchone()
            if director:
                director_id = director[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Director")', (director_name,))
                director_id = cur.lastrowid
            
            # Check if the location already exists, otherwise insert a new one
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid
            
            # Update the Media_Item and DVDs tables
            cur.execute('''
                UPDATE Media_Item
                SET title = ?, genre_id = ?, release_year = ?, creator_id = ?, location_id = ?
                WHERE media_id = ? AND user_id = ?
            ''', (title, genre_id, release_year, director_id, location_id, dvd_id, user_id))
            cur.execute('''
                UPDATE DVDs
                SET runtime = ?, studio = ?, DVD_type = ?
                WHERE media_id = ?
            ''', (runtime, studio, dvd_type, dvd_id))
            conn.commit()
        
        flash('DVD updated successfully.')
        return redirect(url_for('view_dvds'))
    
    return render_template('edit_dvd.html', dvd=dvd, genres=genres, directors=directors, locations=locations)

@app.route('/edit_videogame/<int:videogame_id>', methods=['GET', 'POST'])
def edit_videogame(videogame_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        cur = conn.cursor()
        # Ensure the video game belongs to the logged-in user
        cur.execute('''
            SELECT Media_Item.media_id, Media_Item.title, Media_Item.genre_id, Media_Item.release_year, 
                   VideoGames.console, Media_Creators.name AS developer, Purchase_Locations.loc_name
            FROM Media_Item
            JOIN VideoGames ON Media_Item.media_id = VideoGames.media_id
            JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
            LEFT JOIN Purchase_Locations ON Media_Item.location_id = Purchase_Locations.location_id
            WHERE Media_Item.media_id = ? AND Media_Item.user_id = ?
        ''', (videogame_id, user_id))
        videogame = cur.fetchone()
        
        if not videogame:
            flash('Video game not found or you do not have permission to edit it.')
            return redirect(url_for('view_videogames'))
        
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Designer"')
        developers = [row['name'] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row['loc_name'] for row in cur.fetchall()]
    
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        console = request.form['console']
        developer_name = request.form['developer_input']
        location_name = request.form['location_input']
        
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            
            # Check if the developer already exists, otherwise insert a new one
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Designer"', (developer_name,))
            developer = cur.fetchone()
            if developer:
                developer_id = developer[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Designer")', (developer_name,))
                developer_id = cur.lastrowid
            
            # Check if the location already exists, otherwise insert a new one
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid
            
            # Update the Media_Item and VideoGames tables
            cur.execute('''
                UPDATE Media_Item
                SET title = ?, genre_id = ?, release_year = ?, creator_id = ?, location_id = ?
                WHERE media_id = ? AND user_id = ?
            ''', (title, genre_id, release_year, developer_id, location_id, videogame_id, user_id))
            cur.execute('''
                UPDATE VideoGames
                SET console = ?
                WHERE media_id = ?
            ''', (console, videogame_id))
            conn.commit()
        
        flash('Video game updated successfully.')
        return redirect(url_for('view_videogames'))
    
    return render_template('edit_videogame.html', videogame=videogame, genres=genres, developers=developers, locations=locations)


@app.route('/edit_music/<int:media_id>', methods=['GET', 'POST'])
def edit_music(media_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Fetch base music item
        cur.execute('''
            SELECT Media_Item.*, Albums.album_title, Albums.track_count, Albums.runtime,
                   Media_Creators.name AS creator_name, Media_Creators.type AS creator_type,
                   Purchase_Locations.loc_name, Genres.genre_name,
                   Vinyls.disc_count, CDs.album_id AS cd_album_id, Vinyls.album_id AS vinyl_album_id
            FROM Media_Item
            LEFT JOIN CDs ON Media_Item.media_id = CDs.media_id
            LEFT JOIN Vinyls ON Media_Item.media_id = Vinyls.media_id
            LEFT JOIN Albums ON Albums.album_id = CDs.album_id OR Albums.album_id = Vinyls.album_id
            JOIN Media_Creators ON Media_Item.creator_id = Media_Creators.creator_id
            LEFT JOIN Purchase_Locations ON Media_Item.location_id = Purchase_Locations.location_id
            JOIN Genres ON Media_Item.genre_id = Genres.genre_id
            WHERE Media_Item.media_id = ? AND Media_Item.user_id = ?
        ''', (media_id, user_id))
        
        music = cur.fetchone()

        if not music:
            flash("Music item not found or you don't have permission to edit it.")
            return redirect(url_for('view_music'))

        # Fetch supporting data
        cur.execute('SELECT genre_id, genre_name FROM Genres')
        genres = cur.fetchall()
        cur.execute('SELECT name FROM Media_Creators WHERE type = "Singer/Band"')
        artists = [row['name'] for row in cur.fetchall()]
        cur.execute('SELECT loc_name FROM Purchase_Locations')
        locations = [row['loc_name'] for row in cur.fetchall()]
        # Fetch album_id and associated tracks
        album_id = music['cd_album_id'] or music['vinyl_album_id']
        cur.execute('SELECT track_id, track_name FROM Tracks WHERE album_id = ?', (album_id,))
        tracks = cur.fetchall()

    
    if request.method == 'POST':
        title = request.form['title']
        genre_id = request.form['genre_id']
        release_year = request.form['release_year']
        album_title = request.form['album_title']
        track_count = request.form['track_count']
        runtime = request.form['runtime']
        creator_name = request.form['creator_input']
        location_name = request.form['location_input']
        disc_count = request.form.get('disc_count')

        # Determine media type from original data
        media_type = music['media_type']

        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()

            # Ensure creator exists or insert
            cur.execute('SELECT creator_id FROM Media_Creators WHERE name = ? AND type = "Singer/Band"', (creator_name,))
            creator = cur.fetchone()
            if creator:
                creator_id = creator[0]
            else:
                cur.execute('INSERT INTO Media_Creators (name, type) VALUES (?, "Singer/Band")', (creator_name,))
                creator_id = cur.lastrowid

            # Ensure location exists or insert
            cur.execute('SELECT location_id FROM Purchase_Locations WHERE loc_name = ?', (location_name,))
            location = cur.fetchone()
            if location:
                location_id = location[0]
            else:
                cur.execute('INSERT INTO Purchase_Locations (loc_name) VALUES (?)', (location_name,))
                location_id = cur.lastrowid

            # Update Media_Item
            cur.execute('''
                UPDATE Media_Item
                SET title = ?, genre_id = ?, release_year = ?, creator_id = ?, location_id = ?
                WHERE media_id = ? AND user_id = ?
            ''', (title, genre_id, release_year, creator_id, location_id, media_id, user_id))

            # Update Album
            album_id = music['cd_album_id'] or music['vinyl_album_id']
            cur.execute('''
                UPDATE Albums
                SET album_title = ?, creator_id = ?, track_count = ?, runtime = ?
                WHERE album_id = ?
            ''', (album_title, creator_id, track_count, runtime, album_id))

            # Update Vinyls if applicable
            if media_type == 'Vinyl':
                cur.execute('''
                    UPDATE Vinyls SET disc_count = ? WHERE media_id = ?
                ''', (disc_count, media_id))

            conn.commit()

            # Update Tracks
            track_ids = request.form.getlist('track_id')
            track_names = request.form.getlist('track_name')
            for tid, name in zip(track_ids, track_names):
                if name.strip():
                    cur.execute('UPDATE Tracks SET track_name = ? WHERE track_id = ?', (name.strip(), tid))
                else:
                    # Optionally delete empty ones
                    cur.execute('DELETE FROM Tracks WHERE track_id = ?', (tid,))

            # Insert new tracks
            new_tracks = request.form.getlist('new_track_name')
            album_id = music['cd_album_id'] or music['vinyl_album_id']
            for new_name in new_tracks:
                if new_name.strip():
                    cur.execute('INSERT INTO Tracks (album_id, track_name) VALUES (?, ?)', (album_id, new_name.strip()))

        flash('Music item updated successfully.')
        return redirect(url_for('view_music'))

    return render_template('edit_music.html', music=music, genres=genres, artists=artists, locations=locations, tracks=tracks)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        night_mode = request.form.get('night_mode') == 'on'
        session['night_mode'] = night_mode
        return redirect(url_for('home'))
    
    night_mode = session.get('night_mode', False)
    return render_template('settings.html', night_mode=night_mode)

@app.context_processor
def inject_night_mode():
    return {'night_mode': session.get('night_mode', False)}

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

