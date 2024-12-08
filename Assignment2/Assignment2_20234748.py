import sqlite3

def initialize():
    pass


with sqlite3.connect('Assignment2.db') as db:
    cursor = db.cursor()

    # Create table
    cursor.execute('''
    ''')

    db.commit()

    cursor.close()
