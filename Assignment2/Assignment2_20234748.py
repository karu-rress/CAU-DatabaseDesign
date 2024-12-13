"""
#
# Database Design
#
# Assignment 2: Library Management System
#   20234748 나선우
#
# We don't have a global sqlite3 connection object.
# In real-world applications, lots of users can access the database at the same time.
# If we have a connection for a long time, it can cause a problem.
# So, I've split the connection into short-lived connections.
#
"""

# Import necessary libraries
import argparse
import os
import sqlite3

# Database name
DB_NAME = 'Assignment2.db'

# Global variable to store the current user
# if None, then no user is logged in
# otherwise, it stores the name of the user
current_user = None

# Clears the screen
def clear_screen():
    # UNIX-based and Windows-based systems have different commands
    os.system('cls' if os.name == 'nt' else 'clear')

# Initialize the database
def initialize():
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()

        # Using INTEGER instead of INT for integer types
        # as INTEGER supports autoincrement

        # USER Relation
        cursor.execute('''DROP TABLE IF EXISTS USER;''')
        cursor.execute('''
        CREATE TABLE USER (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(30) NOT NULL,
            email VARCHAR(50) UNIQUE NOT NULL,
            phone VARCHAR(15)
        );''')
        print('USER table created.')

        # LIBRARIAN Relation
        cursor.execute('''DROP TABLE IF EXISTS LIBRARIAN;''')
        cursor.execute('''
        CREATE TABLE LIBRARIAN (
            librarian_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL
        );''')
        print('LIBRARIAN table created.')

        # ROOM Relation
        cursor.execute('''DROP TABLE IF EXISTS ROOM;''')
        cursor.execute('''
        CREATE TABLE ROOM (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name VARCHAR(100) NOT NULL UNIQUE
        );''')
        print('ROOM table created.')

        # LIBRARIAN-ROOM Relation
        # Separated table because LIBRARIAN and ROOM have circular dependency
        cursor.execute('''DROP TABLE IF EXISTS LIBRARIAN_ROOM;''')
        cursor.execute('''
        CREATE TABLE LIBRARIAN_ROOM (
            librarian_id INTEGER NOT NULL UNIQUE,
            room_id INTEGER NOT NULL UNIQUE,
            PRIMARY KEY (librarian_id, room_id),
            FOREIGN KEY (librarian_id) REFERENCES LIBRARIAN(librarian_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        );''')
        print('LIBRARIAN_ROOM table created.')

        # BOOKSHELF Relation
        # num_books must be between 0 and 500, and the default value is 0
        # CASCADE UPDATE for ROOM, as room_id might be changed later
        cursor.execute('''DROP TABLE IF EXISTS BOOKSHELF;''')
        cursor.execute('''
        CREATE TABLE BOOKSHELF (
            bookshelf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category VARCHAR(50) NOT NULL,
            num_books INTEGER DEFAULT 0 CHECK (num_books >= 0 AND num_books <= 500),
            room_id INTEGER NOT NULL,
            FOREIGN KEY (room_id) REFERENCES ROOM(room_id)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );''')
        print('BOOKSHELF table created.')

        # BOOK Relation
        # total_copies must be greater than 0
        # remaining_copies must be between 0 and total_copies
        # Also, if bookshelf_id is same, then category must be same
        # => there is only one (bookshelf_id, category) pair
        cursor.execute('''DROP TABLE IF EXISTS BOOK;''')
        cursor.execute('''
        CREATE TABLE BOOK (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            author VARCHAR(100) NOT NULL,
            publisher VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            total_copies INTEGER NOT NULL CHECK (total_copies >= 1),
            remaining_copies INTEGER NOT NULL CHECK (remaining_copies >= 0 AND remaining_copies <= total_copies),
            librarian_id INTEGER NOT NULL,
            bookshelf_id INTEGER NOT NULL,
            FOREIGN KEY (librarian_id) REFERENCES LIBRARIAN(librarian_id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY (bookshelf_id) REFERENCES BOOKSHELF(bookshelf_id)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );''')
        print('BOOK table created.')

        # BOOK_LOAN Relation
        cursor.execute('''DROP TABLE IF EXISTS BOOK_LOAN;''')
        cursor.execute('''
        CREATE TABLE BOOK_LOAN (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            loan_date DATE NOT NULL,
            return_date DATE,
            FOREIGN KEY (book_id) REFERENCES BOOK(book_id),
            FOREIGN KEY (user_id) REFERENCES USER(user_id)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );''')
        print('BOOK_LOAN table created.')

        # ===================================================================
        #     Triggers
        # ===================================================================

        # when book is inserted, increase num_books
        # and check if the category is the same for the same bookshelf_id
        # (bookshelf_id's are same => category must be same)
        # if not, raise an error
        cursor.execute('''
        CREATE TRIGGER book_added
            BEFORE INSERT ON BOOK FOR EACH ROW BEGIN
                SELECT CASE WHEN EXISTS (
                    SELECT 1 FROM BOOK
                    WHERE bookshelf_id = NEW.bookshelf_id
                    AND category != NEW.category
                ) THEN RAISE(ABORT, 'Each bookshelf_id must have the same category.')
                END;
                UPDATE BOOKSHELF SET num_books = num_books + NEW.total_copies
                WHERE BOOKSHELF.bookshelf_id = NEW.bookshelf_id;
            END;''')

        # when book is deleted, decrease num_books
        cursor.execute('''
        CREATE TRIGGER book_deleted
            AFTER DELETE ON BOOK FOR EACH ROW BEGIN
                UPDATE BOOKSHELF SET num_books = num_books - OLD.total_copies
                WHERE BOOKSHELF.bookshelf_id = OLD.bookshelf_id;
            END;''')

        # A user can only borrow up to 3 books at a time.
        # when book is loaned, decrease remaining_copies
        cursor.execute('''
        CREATE TRIGGER loan_book
            BEFORE INSERT ON BOOK_LOAN FOR EACH ROW BEGIN
                SELECT CASE
                    WHEN (SELECT COUNT(*) FROM BOOK_LOAN WHERE user_id = NEW.user_id AND return_date IS NULL) >= 3
                    THEN RAISE(ABORT, 'A user can only borrow up to 3 books at a time.')
                END;
                UPDATE BOOK SET remaining_copies = remaining_copies - 1
                WHERE book_id = NEW.book_id;
                UPDATE BOOKSHELF SET num_books = num_books - 1
                WHERE bookshelf_id = (SELECT bookshelf_id FROM BOOK WHERE book_id = NEW.book_id);
            END;''')

        # when book is returned, increase remaining_copies
        cursor.execute('''
        CREATE TRIGGER return_book
            AFTER DELETE ON BOOK_LOAN FOR EACH ROW
            BEGIN
                UPDATE BOOK SET remaining_copies = remaining_copies + 1
                WHERE book_id = OLD.book_id;
                UPDATE BOOKSHELF SET num_books = num_books + 1
                WHERE bookshelf_id = (SELECT bookshelf_id FROM BOOK WHERE book_id = OLD.book_id);
            END;''')
        print('Triggers created.')


        db.commit()
        cursor.close()

    print('*** Database initialized successfully. ***', end='\n\n')

# Insert sample data
def insert_sample_data():
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()

        cursor.execute('PRAGMA foreign_keys = ON;')

        # USER
        cursor.execute('''
        INSERT INTO USER (name, email, phone) VALUES
            ('Alice', 'alice@naver.com', '010-1234-5678'),
            ('Bob', 'bob@daum.net', '010-2345-6789'),
            ('Charlie', 'charlie@kakao.com', '010-3456-7890'),
            ('David', 'david@line.net', '010-4567-8901'),
            ('Eve', 'eve@cau.ac.kr', '010-5678-9012'),
            ('Frank', 'frank@outlook.com', '010-6789-0123'),
            ('Grace', 'grace@amazon.com', '010-7890-1234'),
            ('Hannah', 'hannah@samsung.com', '010-8901-2345'),
            ('Ivy', 'ivy@korea.kr', '010-9012-3456');
        ''')
        print('USER data inserted.')

        # LIBRARIAN
        cursor.execute('''
        INSERT INTO LIBRARIAN (name, phone, email) VALUES
            ('Sunwoo', '010-1234-5678', 'nsun527@cau.ac.kr'),
            ('Karu', '010-2345-6789', 'karu-rress@outlook.com');''')
        print('LIBRARIAN data inserted.')

        # ROOM
        cursor.execute('''
        INSERT INTO ROOM (room_name) VALUES
            ('Adult Room'),
            ('Children Room');''')
        print('ROOM data inserted.')

        # LIBRARIAN_ROOM
        cursor.execute('''
        INSERT INTO LIBRARIAN_ROOM (librarian_id, room_id) VALUES
            (1, 1),
            (2, 2);''')
        print('LIBRARIAN_ROOM data inserted.')

        # BOOKSHELF
        cursor.execute('''
        INSERT INTO BOOKSHELF (category, num_books, room_id) VALUES
            ('Computer Science', 3, 1),
            ('Mathematics', 2, 1),
            ('Cartoon', 3, 2),
            ('Fairy Tale', 1, 2);''')
        print('BOOKSHELF data inserted.')

        # BOOK
        cursor.execute('''
        INSERT INTO BOOK (title, author, publisher, category, total_copies, remaining_copies, librarian_id, bookshelf_id) VALUES
            ('Introduction to Algorithms', 'Thomas H. Cormen', 'MIT Press', 'Computer Science', 3, 3, 1, 1),
            ('Programming Language Pragmatics', 'Michael L. Scott', 'Morgan Kaufmann', 'Computer Science', 3, 3, 1, 1),
            ('Computer Networking: A Top-Down Approach', 'James F. Kurose', 'Pearson', 'Computer Science', 3, 3, 1, 1),

            ('Discrete Mathematics and Its Applications', 'Kenneth H. Rosen', 'McGraw-Hill', 'Mathematics', 2, 2, 1, 2),
            ('Linear Algebra and Its Applications', 'David C. Lay', 'Pearson', 'Mathematics', 2, 2, 1, 2),

            ('One Piece', 'Eiichiro Oda', 'Shueisha', 'Cartoon', 5, 5, 2, 3),
            ('Naruto', 'Masashi Kishimoto', 'Shueisha', 'Cartoon', 5, 5, 2, 3),
            ('Attack on Titan', 'Hajime Isayama', 'Kodansha', 'Cartoon', 5, 5, 2, 3),

            ('Alice in Wonderland', 'Lewis Carroll', 'Macmillan', 'Fairy Tale', 4, 4, 2, 4);''')
        print('BOOK data inserted.')

        # BOOK_LOAN
        cursor.execute('''
        INSERT INTO BOOK_LOAN (book_id, user_id, loan_date, return_date) VALUES
            (1, 1, '2024-10-01', '2024-10-15'),
            (2, 2, '2024-10-02', '2024-10-16'),
            (3, 3, '2024-10-03', '2024-10-17'),
            (4, 4, '2024-10-04', '2024-10-18'),
            (5, 5, '2024-10-05', '2024-10-19'),
            (6, 6, '2024-10-06', '2024-10-20'),
            (7, 7, '2024-10-07', NULL),
            (8, 8, '2024-10-08', NULL),
            (9, 9, '2024-10-09', NULL);''')
        print('BOOK_LOAN data inserted.')

        db.commit()
        cursor.close()

    print('*** Sample data inserted successfully. ***', end='\n\n')

# Manages user
def account(type: str):
    global current_user

    # if already logged in
    if current_user is not None:
        print('<< Manage Account >>', end='\n\n')

        print(f'Hello, {current_user}!')
        print('1. Logout')
        print('2. Update Account')
        print('3. Delete Account')
        print('0. Back to the main menu')
        print('-' * 20)
        choice = input('Your choice (0-3) >> ')

        # Get user information
        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            # Using placeholder to prevent SQL injection
            cursor.execute(f'SELECT * FROM {type} WHERE name = ?;', (current_user,))
            user = cursor.fetchone()
            cursor.close()

        # When logout, set current_user to None
        if choice == '1':
            current_user = None
            print('Logged out successfully.')

        # Update Account
        elif choice == '2':
            print('Update Account')

            name = input('Name >> ')
            email = input('Email >> ')
            phone = input('Phone >> ')

            with sqlite3.connect(DB_NAME) as db:
                cursor = db.cursor()
                # Update the user | librarian information
                cursor.execute(f'''UPDATE {type} SET name = ?, email = ?, phone = ?
                               WHERE {'user_id' if type == 'USER' else 'librarian_id'} = ?;''',
                    (name, email, phone, user[0]))
                # Get the updated user | librarian information
                cursor.execute(f'SELECT * FROM {type} WHERE {'user_id' if type == 'USER' else 'librarian_id'} = ?;', (user[0],))
                new_user = cursor.fetchone()
                db.commit()
                cursor.close()

            print('Account updated successfully.')
            print(f'Old: {user}')
            print(f'New: {new_user}')
            current_user = name

        elif choice == '3':
            print('Delete Account')

            with sqlite3.connect(DB_NAME) as db:
                cursor = db.cursor()
                # Enables foreign key constraint
                cursor.execute('PRAGMA foreign_keys = ON;')
                cursor.execute(f'DELETE FROM {type} WHERE {'user_id' if type == 'USER' else 'librarian_id'} = ?;', (user[0],))
                db.commit()
                cursor.close()

            print('Account deleted successfully.')
            current_user = None

        elif choice == '0':
            pass

        else:
            print('Invalid choice. Back to the main menu.', end='\n\n')

        return

    print('<< Login / Register >>', end='\n\n')

    email = input('Email >> ')

    # 1. Check if the email(candidate key) is already registered
    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM {type} WHERE email = ?;', (email,))
        user = cursor.fetchone()
        cursor.close()

    # 2. If registered, login
    if user:
        current_user = user[1]
        print(f'Welcome back, {current_user}!')
        return

    # 3. If not registered, register
    name = input('Name >> ')
    phone = input('Phone >> ')

    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()

        try:
            cursor.execute(f'INSERT INTO {type} (name, email, phone) VALUES (?, ?, ?);', (name, email, phone))
            db.commit()
            current_user = name
            print('Registered successfully.')

        except Exception as e:
            print(f'Error: {e}')

        finally:
            cursor.close()

# Manages book
def book():
    print('<< Manage Book >>', end='\n\n')
    print('1. Add Book')
    print('2. Update Book')
    print('3. Delete Book')
    print('0. Back to the main menu')
    print('-' * 20)
    choice = input('Your choice (0-3) >> ')

    # Add boo
    if choice == '1':
        title = input('Title >> ')
        author = input('Author >> ')
        publisher = input('Publisher >> ')
        category = input('Category >> ')
        total_copies = int(input('Total Copies >> '))
        remaining_copies = total_copies
        librarian_id = int(input('Librarian ID >> '))
        bookshelf_id = int(input('Bookshelf ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('''
            INSERT INTO BOOK (title, author, publisher, category, total_copies, remaining_copies, librarian_id, bookshelf_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);''',
                (title, author, publisher, category, total_copies, remaining_copies, librarian_id, bookshelf_id))
            db.commit()
            cursor.close()
        print('Book added successfully.')

    # Update book
    elif choice == '2':
        book_id = int(input('Book ID >> '))
        title = input('Title >> ')
        author = input('Author >> ')
        publisher = input('Publisher >> ')
        category = input('Category >> ')
        total_copies = int(input('Total Copies >> '))
        remaining_copies = int(input('Remaining Copies >> '))
        librarian_id = int(input('Librarian ID >> '))
        bookshelf_id = int(input('Bookshelf ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('''
            UPDATE BOOK SET title = ?, author = ?, publisher = ?, category = ?, total_copies = ?, remaining_copies = ?, librarian_id = ?, bookshelf_id = ?
            WHERE book_id = ?;''',
                (title, author, publisher, category, total_copies, remaining_copies, librarian_id, bookshelf_id, book_id))
            db.commit()
            cursor.close()
        print('Book updated successfully.')

    # Delete book
    elif choice == '3':
        book_id = int(input('Book ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.execute('DELETE FROM BOOK WHERE book_id = ?;', (book_id,))
            db.commit()
            cursor.close()
        print('Book deleted successfully.')

    elif choice == '0':
        pass

    else:
        print('Invalid choice. Back to the main menu.', end='\n\n')

# Manages room
def room():
    print('<< Manage Room >>', end='\n\n')
    print('1. Add Room')
    print('2. Update Room')
    print('3. Delete Room')
    print('0. Back to the main menu')
    print('-' * 20)
    choice = input('Your choice (0-3) >> ')

    # Add room
    if choice == '1':
        room_name = input('Room Name >> ')
        librarian_id = int(input('Librarian ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            # As we have LIBRARIAN_ROOM separated, we need to insert into both table
            cursor.execute('INSERT INTO ROOM (room_name) VALUES (?);', (room_name,))
            cursor.execute('INSERT INTO LIBRARIAN_ROOM (librarian_id, room_id) VALUES (?, ?);', (librarian_id, cursor.lastrowid))
            db.commit()
            cursor.close()
        print('Room added successfully.')

    # Update room
    elif choice == '2':
        room_id = int(input('Room ID >> '))
        room_name = input('Room Name >> ')
        librarian_id = int(input('Librarian ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            # Enable foreign key constraint
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.execute('DELETE FROM LIBRARIAN_ROOM WHERE room_id = ?;', (room_id,))
            cursor.execute('UPDATE ROOM SET room_name = ? WHERE room_id = ?;', (room_name, room_id))
            cursor.execute('INSERT INTO LIBRARIAN_ROOM (librarian_id, room_id) VALUES (?, ?);', (librarian_id, room_id))
            db.commit()
            cursor.close()
        print('Room updated successfully.')

    # Delete room
    elif choice == '3':
        room_id = int(input('Room ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            # Enable foreign key constraint
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.execute('DELETE FROM LIBRARIAN_ROOM WHERE room_id = ?;', (room_id,))
            cursor.execute('DELETE FROM ROOM WHERE room_id = ?;', (room_id,))
            db.commit()
            cursor.close()
        print('Room deleted successfully.')

    elif choice == '0':
        pass

    else:
        print('Invalid choice. Back to the main menu.', end='\n\n')

# Manages bookshelf
def bookshelf():
    print('<< Manage Bookshelf >>', end='\n\n')
    print('1. Add Bookshelf')
    print('2. Update Bookshelf')
    print('3. Delete Bookshelf')
    print('0. Back to the main menu')
    print('-' * 20)
    choice = input('Your choice (0-3) >> ')

    # Add bookshelf
    if choice == '1':
        category = input('Category >> ')
        room_id = int(input('Room ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('INSERT INTO BOOKSHELF (category, room_id) VALUES (?, ?);', (category, room_id))
            db.commit()
            cursor.close()
        print('Bookshelf added successfully.')

    # Update bookshelf
    elif choice == '2':
        bookshelf_id = int(input('Bookshelf ID >> '))
        category = input('Category >> ')
        num_books = int(input('Number of Books >> '))
        room_id = int(input('Room ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('UPDATE BOOKSHELF SET category = ?, num_books = ?, room_id = ? WHERE bookshelf_id = ?;',
                (category, num_books, room_id, bookshelf_id))
            db.commit()
            cursor.close()
        print('Bookshelf updated successfully.')

    # Delete bookshelf
    elif choice == '3':
        bookshelf_id = int(input('Bookshelf ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.execute('DELETE FROM BOOK WHERE bookshelf_id = ?;', (bookshelf_id,))
            cursor.execute('DELETE FROM BOOKSHELF WHERE bookshelf_id = ?;', (bookshelf_id,))
            db.commit()
            cursor.close()
        print('Bookshelf deleted successfully.')

    elif choice == '0':
        pass

    else:
        print('Invalid choice. Back to the main menu.', end='\n\n')


def loan_return():
    print('<< Loan or Return Book >>', end='\n\n')
    print('1. Loan Book')
    print('2. Return Book')
    print('3. Modify Loan Information')
    print('4. Check User Loan Information')
    print('0. Back to the main menu')
    print('-' * 20)
    choice = input('Your choice (0-2) >> ')

    # Loan book
    if choice == '1':
        book_id = int(input('Book ID >> '))
        user_id = int(input('User ID >> '))
        # Of course, we can use datetime library to get the current date,
        # but as this is a management system, so we can manually input the date
        loan_date = input('Loan Date (YYYY-MM-DD) >> ')

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            # NOTE: return_date is default NULL
            cursor.execute('INSERT INTO BOOK_LOAN (book_id, user_id, loan_date) VALUES (?, ?, ?);',
                (book_id, user_id, loan_date))
            db.commit()
            cursor.close()
        print('Book loaned successfully.')

    # Return book
    elif choice == '2':
        loan_id = int(input('Loan ID >> '))
        return_date = input('Return Date (YYYY-MM-DD) >> ')

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            # NOTE: not deleting the row, just updating the return_date
            # so that we can keep the history of the loan
            cursor.execute('UPDATE BOOK_LOAN SET return_date = ? WHERE loan_id = ?;', (return_date, loan_id))
            db.commit()
            cursor.close()
        print('Book returned successfully.')

    # Modify loan information
    elif choice == '3':
        loan_id = int(input('Loan ID >> '))
        book_id = int(input('Book ID >> '))
        user_id = int(input('User ID >> '))
        loan_date = input('Loan Date (YYYY-MM-DD) >> ')
        return_date = input('Return Date (YYYY-MM-DD) >> ')

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('UPDATE BOOK_LOAN SET book_id = ?, user_id = ?, loan_date = ?, return_date = ? WHERE loan_id = ?;',
                (book_id, user_id, loan_date, return_date, loan_id))
            db.commit()
            cursor.close()
        print('Loan information modified successfully.')

    # With user's ID, check the loan information
    elif choice == '4':
        user_id = int(input('User ID >> '))

        with sqlite3.connect(DB_NAME) as db:
            cursor = db.cursor()
            cursor.execute('''
            SELECT loan_id, title, loan_date, return_date
            FROM BOOK_LOAN
            JOIN BOOK USING (book_id)
            WHERE user_id = ?;''', (user_id,))
            loan_info = cursor.fetchall()
            cursor.close()

        print(f'Loan Information for User ID {user_id}')
        print('-' * 20)
        for loan in loan_info:
            print(loan)

    elif choice == '0':
        pass

    else:
        print('Invalid choice. Back to the main menu.', end='\n\n')



# Prints all the data in the database
def DEBUG():
    def select_and_fetch(cursor: sqlite3.Cursor, table: str):
        cursor.execute(f'SELECT * FROM {table}')
        return cursor.fetchall()

    tables = ['USER', 'LIBRARIAN', 'ROOM', 'BOOKSHELF', 'BOOK', 'BOOK_LOAN']
    data = {}

    with sqlite3.connect(DB_NAME) as db:
        cursor = db.cursor()
        for table in tables:
            data[table] = select_and_fetch(cursor, table)
        cursor.close()

    print('<< DEBUG MODE >>', end='\n\n')

    for table, rows in data.items():
        print(f'\n>>========== {table}')
        for row in rows:
            print(row)


if __name__ == '__main__':
    clear_screen()

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--skip-initialize', action='store_true')
    parser.add_argument('-n', '--no-sample-data', action='store_true')
    args = parser.parse_args()

    # if -s or --skip-initialize is provided, skip the initialization
    if args.skip_initialize and args.no_sample_data:
        print("Warning: '--no-sample-data' option is ignored because '--skip-initialize' option is provided.", end='\n\n')

    elif not args.skip_initialize: # initialize the database
        print("'-s' option is not provided.\nInitializing the database...", end='\n\n')
        initialize()

        if not args.no_sample_data:
            insert_sample_data()
        else:
            print("'-n' option is provided.\nSkipping the sample data insertion.", end='\n\n')

    else: # skip the initialization
        print("'-s' option is provided.\nSkipping the initialization.", end='\n\n')


    print("\nWelcome to Sunwoo's Library!", end='\n\n')

    while True:
        try:
            print(f'Welcome, {current_user}' if current_user else 'Please login or register first', end='\n\n')
            print(f'<< Main Menu >>', end='\n\n')
            print('1. Login / Register or Manage User Account')
            print('2. Login / Register or Manage Librarian Account')
            print('3. Manage Room')
            print('4. Manage Bookshelf')
            print('5. Manage Book')
            print('6. Loan or Return Book')
            print('7. DEBUG MODE')
            print('0. Exit')
            print('=' * 50)

            choice = input('Your choice (0-7) >> ')

            if choice == '1':
                account("USER")
            elif choice == '2':
                account("LIBRARIAN")
            elif choice == '3':
                room()
            elif choice == '4':
                bookshelf()
            elif choice == '5':
                book()
            elif choice == '6':
                loan_return()
            elif choice == '7':
                DEBUG()
            elif choice == '0':
                print('Goodbye!')
                exit(0)
            else:
                print('Invalid choice. Please try again.', end='\n\n')
                continue

            print()
            print('Press Enter to back to the main menu...')
            input()
            clear_screen()

        except Exception as e:
            print(f'Error: {e}')
            print('Please try again.', end='\n\n')
            input()
            clear_screen()

