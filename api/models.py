import sqlite3
import os
from os import path

# Define the ROOT directory as the location of the current file
# '__file__' is available when the script is run directly or imported.
ROOT = path.dirname(path.abspath(__file__))

def create_post(name, content):
    """Inserts a new post into the 'posts' table."""
    # 1. Use 'sqlite3' for the module, not 'sql'
    # 2. Use 'with' statement for connection management (safer and automatic close)
    with sqlite3.connect(path.join(ROOT, 'database.db')) as con:
        curr = con.cursor()
        
        # 3. Typo: 'excute' should be 'execute'
        # 4. Parameters should be a TUPLE or a LIST, not a SET (curly braces {name, content} are a set)
        curr.execute("INSERT INTO posts (name, content) VALUES (?, ?)", (name, content,))
        
        # 5. commit() is inside the 'with' block, ensuring it only happens on success
        # The 'with' statement automatically handles con.close()
        con.commit()


def get_posts():
    """Retrieves all posts from the 'posts' table."""
    # Use 'with' statement for connection management
    with sqlite3.connect(path.join(ROOT, 'database.db')) as con:
        curr = con.cursor()
        curr.execute('SELECT * FROM posts')
        
        # 6. Typo: 'cur' should be 'curr' (the cursor variable name)
        posts = curr.fetchall()
        return posts