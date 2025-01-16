import sqlite3

conn = sqlite3.connect("Personal_cateloguedb.db")
cur = conn.cursor()

conn.executescript('''
    CREATE TABLE IF NOT EXISTS books (
  book_id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  publishing_year_id INTEGER,
  description TEXT,
  notes TEXT,
  genre_id INTEGER,
  media_id INTEGER NOT NULL,
  purchase_id INTEGER,
  FOREIGN KEY (genre_id) REFERENCES genres(genre_id),
  FOREIGN KEY (media_id) REFERENCES media_type(media_id),
  FOREIGN KEY (publishing_year_id) REFERENCES publishing_year(publishing_year_id),
  FOREIGN KEY (purchase_id) REFERENCES purchase(purchase_id)
);''')
