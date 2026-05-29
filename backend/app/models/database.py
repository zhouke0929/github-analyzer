"""SQLite数据库管理"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "./data/analyzer.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    repo_url TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    repo_info TEXT,
                    readme_cn TEXT,
                    summary TEXT,
                    tech_stack TEXT,
                    architecture TEXT,
                    issues_analysis TEXT,
                    analysis_mode TEXT DEFAULT 'quick',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            conn.commit()

            # 检查是否需要添加新字段（兼容旧数据库）
            self._migrate_db(conn)
        finally:
            conn.close()

    def _migrate_db(self, conn: sqlite3.Connection):
        """数据库迁移 - 添加新字段"""
        try:
            # 获取表结构
            cursor = conn.execute("PRAGMA table_info(analyses)")
            columns = [row[1] for row in cursor.fetchall()]

            # 添加缺失的字段
            if "architecture" not in columns:
                conn.execute("ALTER TABLE analyses ADD COLUMN architecture TEXT")
                print("[数据库迁移] 添加 architecture 字段")

            if "issues_analysis" not in columns:
                conn.execute("ALTER TABLE analyses ADD COLUMN issues_analysis TEXT")
                print("[数据库迁移] 添加 issues_analysis 字段")

            if "analysis_mode" not in columns:
                conn.execute("ALTER TABLE analyses ADD COLUMN analysis_mode TEXT DEFAULT 'quick'")
                print("[数据库迁移] 添加 analysis_mode 字段")

            conn.commit()
        except Exception as e:
            print(f"[数据库迁移] {type(e).__name__}: {str(e)}")

    def create_analysis(self, analysis_id: str, repo_url: str, owner: str, repo_name: str, repo_info: dict) -> dict:
        """创建分析记录"""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO analyses (id, repo_url, owner, repo_name, status, repo_info) VALUES (?, ?, ?, ?, ?, ?)",
                (analysis_id, repo_url, owner, repo_name, "pending", json.dumps(repo_info, ensure_ascii=False))
            )
            conn.commit()
            return {"id": analysis_id, "status": "pending", "repo_info": repo_info}
        finally:
            conn.close()

    def get_analysis(self, analysis_id: str) -> dict | None:
        """获取分析记录"""
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_analysis_by_repo(self, owner: str, repo_name: str) -> dict | None:
        """根据仓库信息获取最新的分析记录"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM analyses WHERE owner = ? AND repo_name = ? ORDER BY created_at DESC LIMIT 1",
                (owner, repo_name)
            ).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_all_projects(self) -> list:
        """获取所有已分析的项目（每个项目只返回最新记录）"""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT * FROM analyses
                WHERE status = 'completed'
                AND id IN (
                    SELECT id FROM analyses
                    WHERE status = 'completed'
                    GROUP BY owner, repo_name
                    HAVING created_at = MAX(created_at)
                )
                ORDER BY created_at DESC
            """).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_analysis(self, analysis_id: str) -> bool:
        """删除分析记录"""
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def update_status(self, analysis_id: str, status: str, error_message: str = None, current_step: str = None):
        """更新分析状态"""
        conn = self._get_conn()
        try:
            if status == "completed":
                conn.execute(
                    "UPDATE analyses SET status = ?, completed_at = ? WHERE id = ?",
                    (status, datetime.now().isoformat(), analysis_id)
                )
            elif status == "failed":
                conn.execute(
                    "UPDATE analyses SET status = ?, error_message = ? WHERE id = ?",
                    (status, error_message, analysis_id)
                )
            else:
                # 将当前步骤信息存储在 error_message 字段中（复用字段用于进度追踪）
                conn.execute(
                    "UPDATE analyses SET status = ?, error_message = ? WHERE id = ?",
                    (status, current_step or status, analysis_id)
                )
            conn.commit()
        finally:
            conn.close()

    def update_result(self, analysis_id: str, **kwargs):
        """更新分析结果"""
        conn = self._get_conn()
        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    updates.append(f"{key} = ?")
                    values.append(value)

            if updates:
                values.append(analysis_id)
                sql = f"UPDATE analyses SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, values)
                conn.commit()
        finally:
            conn.close()


# 全局数据库实例
db = Database()
