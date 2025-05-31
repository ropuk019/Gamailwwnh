import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            pending_balance REAL DEFAULT 0,
            referrer_id INTEGER,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users (user_id)
        )
        ''')
        
        # Gmail accounts table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS gmails (
            gmail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            password TEXT,
            recovery_email TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        ''')
        
        # Pending gmails table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_gmails (
            pending_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            password TEXT,
            recovery_email TEXT,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Withdrawals table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            withdrawal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone_number TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Transactions table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()

    def user_exists(self, user_id):
        self.cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        return bool(self.cursor.fetchone())

    def add_user(self, user_id, username, referrer_id=None):
        self.cursor.execute('''
        INSERT INTO users (user_id, username, referrer_id)
        VALUES (?, ?, ?)
        ''', (user_id, username, referrer_id))
        self.conn.commit()

    def get_username(self, user_id):
        self.cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_gmail(self, user_id, email, password, recovery_email):
        self.cursor.execute('''
        INSERT INTO gmails (user_id, email, password, recovery_email)
        VALUES (?, ?, ?, ?)
        ''', (user_id, email, password, recovery_email))
        self.conn.commit()

    def add_pending_gmail(self, user_id, email, password, recovery_email):
        self.cursor.execute('''
        INSERT INTO pending_gmails (user_id, email, password, recovery_email)
        VALUES (?, ?, ?, ?)
        ''', (user_id, email, password, recovery_email))
        self.conn.commit()

    def get_pending_gmail(self, pending_id):
        self.cursor.execute('''
        SELECT user_id, email, password, recovery_email FROM pending_gmails
        WHERE pending_id = ?
        ''', (pending_id,))
        return self.cursor.fetchone()

    def remove_pending_gmail(self, pending_id):
        self.cursor.execute('DELETE FROM pending_gmails WHERE pending_id = ?', (pending_id,))
        self.conn.commit()

    def get_pending_gmails(self):
        self.cursor.execute('''
        SELECT p.pending_id, u.username, p.email, p.submission_date
        FROM pending_gmails p
        JOIN users u ON p.user_id = u.user_id
        ORDER BY p.submission_date
        ''')
        return self.cursor.fetchall()

    def get_user_gmails(self, user_id):
        self.cursor.execute('''
        SELECT gmail_id, email, password, recovery_email FROM gmails
        WHERE user_id = ?
        ORDER BY registration_date DESC
        ''', (user_id,))
        return self.cursor.fetchall()

    def update_balance(self, user_id, amount):
        # Update balance
        self.cursor.execute('''
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        ''', (amount, user_id))
        
        # Record transaction
        transaction_type = 'credit' if amount > 0 else 'debit'
        description = 'Gmail sale' if amount > 0 else 'Withdrawal'
        
        self.cursor.execute('''
        INSERT INTO transactions (user_id, amount, type, description)
        VALUES (?, ?, ?, ?)
        ''', (user_id, abs(amount), transaction_type, description))
        
        self.conn.commit()

    def get_balance(self, user_id):
        self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_pending_balance(self, user_id):
        self.cursor.execute('SELECT COUNT(*) * 0.05 FROM pending_gmails WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_referrals(self, user_id):
        self.cursor.execute('''
        SELECT u.user_id, u.username, SUM(t.amount * 0.05) as earnings
        FROM users u
        LEFT JOIN transactions t ON u.user_id = t.user_id AND t.type = 'credit'
        WHERE u.referrer_id = ?
        GROUP BY u.user_id, u.username
        ''', (user_id,))
        return self.cursor.fetchall()

    def get_referral_count(self, user_id):
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
        return self.cursor.fetchone()[0]

    def get_referral_earnings(self, user_id):
        self.cursor.execute('''
        SELECT SUM(t.amount * 0.05)
        FROM users u
        JOIN transactions t ON u.user_id = t.user_id AND t.type = 'credit'
        WHERE u.referrer_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0

    def add_withdrawal(self, user_id, phone_number, amount):
        self.cursor.execute('''
        INSERT INTO withdrawals (user_id, phone_number, amount)
        VALUES (?, ?, ?)
        ''', (user_id, phone_number, amount))
        self.conn.commit()

    def close(self):
        self.conn.close()