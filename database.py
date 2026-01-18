import os
import json
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any, Union
import pandas as pd

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

class TursoHTTPCursor:
    def __init__(self, connection):
        self.connection = connection
        self.lastrowid = None
        self.rowcount = -1
        self.rows = []
        self.columns = []
        self.row_index = 0

    def execute(self, sql: str, parameters: tuple = ()) -> 'TursoHTTPCursor':
        # Prepare arguments
        args = []
        for param in parameters:
            if param is None:
                args.append({"type": "null"})
            elif isinstance(param, int):
                args.append({"type": "integer", "value": str(param)})
            elif isinstance(param, float):
                args.append({"type": "float", "value": param})
            elif isinstance(param, (str, datetime)):
                args.append({"type": "text", "value": str(param)})
            elif isinstance(param, bytes):
                # Simple blob support if needed
                args.append({"type": "blob", "base64": base64.b64encode(param).decode('utf-8')})
            else:
                # Fallback to string
                args.append({"type": "text", "value": str(param)})

        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": args
                    }
                },
                {
                    "type": "close"
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.connection.token}",
            "Content-Type": "application/json"
        }

        # Construct URL correctly
        url = self.connection.url
        if not url.endswith('/v2/pipeline'):
            if url.endswith('/'):
                url = url + 'v2/pipeline'
            else:
                url = url + '/v2/pipeline'
        
        # Handle libsql:// protocol replacement if present
        url = url.replace("libsql://", "https://")

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Reset state
            self.rows = []
            self.columns = []
            self.row_index = 0
            self.lastrowid = None # Not always available in HTTP API easily without extra query
            
            # Parse results
            results = data.get("results", [])
            if results:
                # First result corresponds to execute
                exec_result = results[0]
                if exec_result.get("type") == "ok":
                    resp = exec_result.get("response", {})
                    
                    # Columns
                    cols = resp.get("cols", [])
                    self.columns = [c["name"] for c in cols]
                    
                    # Rows
                    result_rows = resp.get("rows", [])
                    parsed_rows = []
                    for row in result_rows:
                        parsed_row = []
                        for cell in row:
                            val = cell.get("value")
                            if cell.get("type") == "integer":
                                val = int(val)
                            elif cell.get("type") == "float":
                                val = float(val)
                            elif cell.get("type") == "blob":
                                val = base64.b64decode(val)
                            # text and null are handled naturally
                            parsed_row.append(val)
                        parsed_rows.append(tuple(parsed_row))
                    
                    self.rows = parsed_rows
                    self.rowcount = len(parsed_rows)
                    
                    # For INSERTs, we might need last_insert_rowid() if using it.
                    # Standard SQL doesn't return it in response unless RETURNING is used
                    # or separate query. For now, we ignore lastrowid or use RETURNING.
                    # Current app usages:
                    # add_task -> uses cursor.lastrowid
                    # record_spin -> uses cursor.lastrowid
                    
                    # If it was an INSERT, we need to handle lastrowid.
                    # Since we can't easily get it from standard response without RETURNING,
                    # We might need to modify queries or run a second query in the same pipeline.
        except Exception as e:
            print(f"Turso HTTP Error: {e}")
            raise e

        return self

    def fetchone(self) -> Optional[Union[Dict, Tuple]]:
        if self.row_index < len(self.rows):
            row = self.rows[self.row_index]
            self.row_index += 1
            if self.connection.row_factory:
                # Basic row factory simulation (sqlite3.Row)
                # We need a dict-like object
                return dict(zip(self.columns, row))
            return row
        return None

    def fetchall(self) -> List[Union[Dict, Tuple]]:
        remaining = self.rows[self.row_index:]
        self.row_index = len(self.rows)
        if self.connection.row_factory:
            return [dict(zip(self.columns, r)) for r in remaining]
        return remaining

    def close(self):
        pass

class TursoHTTPConnection:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.row_factory = None

    def cursor(self):
        return TursoHTTPCursor(self)

    def commit(self):
        # HTTP API is auto-commit for single requests usually
        pass

    def close(self):
        pass

class TaskDatabase:
    def __init__(self, db_path: str = "task_spinner.db"):
        self.db_path = db_path
        self.use_turso = False
        self.turso_url = None
        self.turso_token = None
        
        if STREAMLIT_AVAILABLE and REQUESTS_AVAILABLE:
            try:
                # Check secrets first
                if "turso" in st.secrets:
                    self.turso_url = st.secrets["turso"]["database_url"]
                    self.turso_token = st.secrets["turso"]["auth_token"]
                    self.use_turso = True
                    print("✅ Connected to Turso database (HTTP Mode)")
            except Exception as e:
                print(f"⚠️  Turso secrets not found, using local SQLite: {e}")
        
        if not self.use_turso:
            print(f"📁 Using local SQLite database: {db_path}")
        
        self.init_database()
    
    def get_connection(self):
        if self.use_turso:
            return TursoHTTPConnection(self.turso_url, self.turso_token)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if tables exist
        # SQLite: SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';
        # Turso: same
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_name TEXT NOT NULL,
                        category TEXT DEFAULT 'General',
                        priority INTEGER DEFAULT 1,
                        active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spin_history'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS spin_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER NOT NULL,
                        spun_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed INTEGER DEFAULT 0,
                        notes TEXT,
                        FOREIGN KEY (task_id) REFERENCES tasks (id)
                    )
                """)
            conn.commit()
        except Exception as e:
            print(f"Init DB Error: {e}")
            
        conn.close()
    
    def add_task(self, task_name: str, category: str = "General", priority: int = 1) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Uses RETURNING id for Turso (since lastrowid helper is hard in HTTP)
        # SQLite 3.35+ supports RETURNING. Turso supports it.
        # But local SQLite might be old.
        # We handle both.
        
        if self.use_turso:
            sql = "INSERT INTO tasks (task_name, category, priority) VALUES (?, ?, ?) RETURNING id"
            cursor.execute(sql, (task_name, category, priority))
            row = cursor.fetchone()
            # row might be dict or tuple
            if isinstance(row, dict):
                task_id = row['id']
            else:
                task_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO tasks (task_name, category, priority) VALUES (?, ?, ?)",
                (task_name, category, priority)
            )
            task_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return task_id
    
    def get_all_tasks(self, active_only: bool = True) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM tasks WHERE active = 1 ORDER BY priority DESC, task_name")
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY priority DESC, task_name")
        
        # If Turso, rows are already dicts if row_factory logic worked or handled in method
        # My TursoHTTPCursor.fetchall converts to dict if self.connection.row_factory is set
        # But wait, I set row_factory=None in __init__ of TursoHTTPConnection
        # I should simulate it.
        
        rows = cursor.fetchall()
        
        # Normalize to list of dicts
        tasks = []
        for row in rows:
            if isinstance(row, dict):
                tasks.append(row)
            else:
                # Should not happen if I use row_factory=sqlite3.Row logic or my custom dict converter
                # Local SQLite with row_factory returns sqlite3.Row which is dict-like
                tasks.append(dict(row))
                
        conn.close()
        return tasks
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_task(self, task_id: int, task_name: str = None, 
                   category: str = None, priority: int = None, active: bool = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if task_name is not None:
            updates.append("task_name = ?")
            params.append(task_name)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if active is not None:
            updates.append("active = ?")
            params.append(1 if active else 0)
        
        if updates:
            params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, tuple(params))
            conn.commit()
        
        conn.close()
    
    def delete_task(self, task_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET active = 0 WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
    
    def get_task_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE active = 1")
        row = cursor.fetchone()
        if isinstance(row, dict):
            count = row['count']
        elif hasattr(row, 'keys'): # sqlite3.Row
            count = row['count']
        else:
            count = row[0]
        conn.close()
        return count
    
    def record_spin(self, task_id: int, notes: str = "") -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.use_turso:
            sql = "INSERT INTO spin_history (task_id, notes) VALUES (?, ?) RETURNING id"
            cursor.execute(sql, (task_id, notes))
            row = cursor.fetchone()
            if isinstance(row, dict):
                spin_id = row['id']
            else:
                spin_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO spin_history (task_id, notes) VALUES (?, ?)",
                (task_id, notes)
            )
            spin_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return spin_id
    
    def mark_spin_completed(self, spin_id: int, completed: bool = True):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE spin_history SET completed = ? WHERE id = ?",
            (1 if completed else 0, spin_id)
        )
        conn.commit()
        conn.close()
    
    def get_spin_history(self, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sh.*, t.task_name, t.category, t.priority
            FROM spin_history sh
            JOIN tasks t ON sh.task_id = t.id
            ORDER BY sh.spun_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
        conn.close()
        return history
    
    def get_analytics_data(self, days: int = 30) -> pd.DataFrame:
        conn = self.get_connection()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # For HTTP client, we need to adapt since pandas read_sql_query expects a real sqlalchemy or DBAPI connection
        # TursoHTTPConnection is NOT fully DBAPI compliant.
        # So we should manually fetch and create DataFrame if using Turso.
        
        query = """
            SELECT 
                sh.spun_at,
                sh.completed,
                t.task_name,
                t.category,
                t.priority,
                DATE(sh.spun_at) as spin_date
            FROM spin_history sh
            JOIN tasks t ON sh.task_id = t.id
            WHERE sh.spun_at >= ?
            ORDER BY sh.spun_at
        """
        
        if self.use_turso:
            cursor = conn.cursor()
            cursor.execute(query, (str(cutoff_date),)) # Ensure string for date
            rows = cursor.fetchall()
            # Convert list of dicts/rows to DF
            if not rows:
                df = pd.DataFrame(columns=['spun_at', 'completed', 'task_name', 'category', 'priority', 'spin_date'])
            else:
                # rows are usually dicts from my cursor
                df = pd.DataFrame([dict(r) for r in rows])
        else:
            df = pd.read_sql_query(query, conn, params=(cutoff_date,))
            
        conn.close()
        return df
    
    def get_task_frequency(self) -> List[Tuple[str, int]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.task_name, COUNT(sh.id) as spin_count
            FROM tasks t
            LEFT JOIN spin_history sh ON t.id = sh.task_id
            WHERE t.active = 1
            GROUP BY t.id, t.task_name
            ORDER BY spin_count DESC
        """)
        result = cursor.fetchall()
        conn.close()
        
        # Result items might be dicts or tuples
        output = []
        for row in result:
            if isinstance(row, dict):
                output.append((row['task_name'], row['spin_count']))
            else:
                output.append((row[0], row[1]))
        return output
    
    def get_completion_rate(self) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM spin_history WHERE completed = 1")
        row = cursor.fetchone()
        completed = row['count'] if isinstance(row, dict) else row[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM spin_history")
        row = cursor.fetchone()
        total = row['count'] if isinstance(row, dict) else row[0]
        
        conn.close()
        return (completed / total * 100) if total > 0 else 0
    
    def get_category_stats(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.category,
                COUNT(sh.id) as total_spins,
                SUM(sh.completed) as completed_spins
            FROM tasks t
            LEFT JOIN spin_history sh ON t.id = sh.task_id
            WHERE t.active = 1
            GROUP BY t.category
            ORDER BY total_spins DESC
        """)
        
        rows = cursor.fetchall()
        stats = []
        for row in rows:
            if isinstance(row, dict):
                 stats.append({"category": row['category'], "total": row['total_spins'], "completed": row['completed_spins']})
            else:
                 stats.append({"category": row[0], "total": row[1], "completed": row[2]})
                 
        conn.close()
        return stats
