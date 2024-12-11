import sqlite3
import os

def initialize():
    with sqlite3.connect('Assignment2.db') as db:
        cursor = db.cursor()

        # USER Relation
        cursor.execute('''
        CREATE TABLE USER (
            user_id INTEGER PRIMARY KEY,
            name VARCHAR(30) NOT NULL,
            email VARCHAR(50) UNIQUE NOT NULL,
            phone VARCHAR(15)
        );
        ''')

        # LIBRARIAN Relation
        cursor.execute('''
        CREATE TABLE LIBRARIAN (
            librarian_id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            room_id INTEGER,
        );
        ''') # Add foreign key later

        # ROOM Relation
        cursor.execute('''
        CREATE TABLE ROOM (
            room_id INTEGER PRIMARY KEY,
            room_name VARCHAR(100) NOT NULL UNIQUE,
            librarian_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (librarian_id) REFERENCES LIBRARIAN(librarian_id)
        );
        ''') # Add foreign key later

        # Add foreign key
        cursor.execute('''
        ALTER TABLE LIBRARIAN
        ADD FOREIGN KEY (room_id) REFERENCES ROOM(room_id);
        ''')

        # BOOKSHELF Relation
        cursor.execute('''
        CREATE TABLE BOOKSHELF (
            bookshelf_id INTEGER PRIMARY KEY,
            category VARCHAR(50) NOT NULL UNIQUE,
            num_books INTEGER DEFAULT 0 CHECK (num_books >= 0 AND num_books <= 500),
            room_id INTEGER NOT NULL,
            FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
        );
        ''')

        # ROOM-BOOKSHELF Relation
        cursor.execute('''
        CREATE TABLE ROOM_BOOKSHELF (
            room_id INTEGER NOT NULL,
            bookshelf_id INTEGER NOT NULL,
            PRIMARY KEY (room_id, bookshelf_id),
            FOREIGN KEY (room_id) REFERENCES ROOM(room_id),
            FOREIGN KEY (bookshelf_id) REFERENCES BOOKSHELF(bookshelf_id)
        );
        ''')

        # BOOK Relation
        cursor.execute('''
        CREATE TABLE BOOK (
            book_id INTEGER PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            publisher VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            total_copies INTEGER NOT NULL CHECK (total_copies >= 1),
            remaining_copies INTEGER NOT NULL CHECK (remaining_copies >= 0 AND remaining_copies <= total_copies),
            librarian_id INTEGER NOT NULL,
            bookshelf_id INTEGER NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (librarian_id) REFERENCES LIBRARIAN(librarian_id),
            FOREIGN KEY (bookshelf_id) REFERENCES BOOKSHELF(bookshelf_id),
            FOREIGN KEY (user_id) REFERENCES USER(user_id)
        );
        ''')

        # BOOKSHELF_BOOK Relation
        cursor.execute('''
        CREATE TABLE BOOKSHELF_BOOK (
            bookshelf_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            PRIMARY KEY (bookshelf_id, book_id),
            FOREIGN KEY (bookshelf_id) REFERENCES BOOKSHELF(bookshelf_id),
            FOREIGN KEY (book_id) REFERENCES BOOK(book_id)
        );
        ''')

        # BOOK_LOAN Relation
        cursor.execute('''
        CREATE TABLE BOOK_LOAN (
            loan_id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            loan_date DATE NOT NULL,
            return_date DATE,
            FOREIGN KEY (book_id) REFERENCES BOOK(book_id),
            FOREIGN KEY (user_id) REFERENCES USER(user_id),
            CHECK ((SELECT COUNT(*) FROM BOOK_LOAN WHERE user_id = USER.user_id) <= 3)
        );
        ''')

        db.commit()
        cursor.close()

def new_user():
    pass

def new_book():
    pass

def update_book():
    pass

def delete_book():
    pass

def loan_book():
    pass

def return_book():
    pass

if __name__ == '__main__':
    initialize()
    print("Welcome to Sunwoo's Library!", end='\n\n')

    while True:
        print('<< Main Menu >>', end='\n\n')
        print('1. Register New User')
        print('2. Register New Book')
        print('3. Update Book Information')
        print('4. Delete Book')
        print('5. Loan Book')
        print('6. Return Book')
        print('7. Exit', end='\n\n')

        choice = input('Your choice (1-7) >> ')

        if choice == '1':
            new_user()
        elif choice == '2':
            new_book()
        elif choice == '3':
            update_book()
        elif choice == '4':
            delete_book()
        elif choice == '5':
            loan_book()
        elif choice == '6':
            return_book()
        elif choice == '7':
            print('Goodbye!')
            break
        else:
            print('Invalid choice. Please try again.', end='\n\n')
            continue

        print()
        print('Press Enter to back to the main menu...')
        input()
        os.system('clear')
