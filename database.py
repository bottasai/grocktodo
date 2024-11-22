import sqlite3
from datetime import datetime

class TodoDatabase:
    def __init__(self, db_name='todos.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        # Create todos table if it doesn't exist
        c.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                datetime TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_todo(self, description, datetime_str):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute(
            'INSERT INTO todos (description, datetime) VALUES (?, ?)',
            (description, datetime_str)
        )
        
        conn.commit()
        todo_id = c.lastrowid
        conn.close()
        
        return todo_id

    def get_all_todos(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('SELECT id, description, datetime, completed, created_at FROM todos ORDER BY datetime')
        
        todos = []
        for row in c.fetchall():
            todos.append({
                'id': row[0],
                'description': row[1],
                'datetime': row[2],
                'completed': bool(row[3]),
                'created_at': row[4]
            })
        
        conn.close()
        return todos

    def get_todo(self, todo_id):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute(
            'SELECT id, description, datetime, completed, created_at FROM todos WHERE id = ?',
            (todo_id,)
        )
        
        row = c.fetchone()
        if row:
            todo = {
                'id': row[0],
                'description': row[1],
                'datetime': row[2],
                'completed': bool(row[3]),
                'created_at': row[4]
            }
        else:
            todo = None
        
        conn.close()
        return todo

    def update_todo_description(self, todo_id, new_description):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute(
            'UPDATE todos SET description = ? WHERE id = ?',
            (new_description, todo_id)
        )
        
        conn.commit()
        conn.close()

    def delete_todo(self, todo_id):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        
        conn.commit()
        conn.close()

    def toggle_todo(self, todo_id):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute(
            'UPDATE todos SET completed = NOT completed WHERE id = ?',
            (todo_id,)
        )
        
        conn.commit()
        conn.close()

    def clear_all_todos(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('DELETE FROM todos')
        
        conn.commit()
        conn.close()
