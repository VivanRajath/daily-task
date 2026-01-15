import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd

class TaskDatabase:
    def __init__(self, db_path: str = "task_spinner.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
        conn.close()
    
    def add_task(self, task_name: str, category: str = "General", priority: int = 1) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
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
        
        tasks = [dict(row) for row in cursor.fetchall()]
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
            cursor.execute(query, params)
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
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE active = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def record_spin(self, task_id: int, notes: str = "") -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
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
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    
    def get_analytics_data(self, days: int = 30) -> pd.DataFrame:
        conn = self.get_connection()
        cutoff_date = datetime.now() - timedelta(days=days)
        
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
        return [(row[0], row[1]) for row in result]
    
    def get_completion_rate(self) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM spin_history WHERE completed = 1")
        completed = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM spin_history")
        total = cursor.fetchone()[0]
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
        stats = [{"category": row[0], "total": row[1], "completed": row[2]} 
                for row in cursor.fetchall()]
        conn.close()
        return stats
