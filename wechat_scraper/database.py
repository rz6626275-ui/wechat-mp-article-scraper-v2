import sqlite3
import json
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="data/wechat_scraper.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 公众号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                fakeid TEXT,
                nickname TEXT,
                alias TEXT,
                first_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scraped_at TIMESTAMP,
                total_articles INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        ''')
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                cover_url TEXT,
                publish_date TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                downloaded BOOLEAN DEFAULT 0,
                local_path TEXT,
                image_count INTEGER DEFAULT 0,
                read_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                content TEXT,
                is_favorite BOOLEAN DEFAULT 0,
                is_read BOOLEAN DEFAULT 0,
                tags TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT,
                type TEXT,
                pages INTEGER,
                status TEXT,
                total_articles INTEGER DEFAULT 0,
                downloaded_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Rate limits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reset_time TIMESTAMP
            )
        ''')
        
        # 创建索引以提升查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_content ON articles(content)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_publish_date ON articles(publish_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_account_id ON articles(account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_downloaded ON articles(downloaded)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_is_favorite ON articles(is_favorite)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_is_read ON articles(is_read)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_name ON accounts(name)')
        
        conn.commit()
        conn.close()
    
    # ========== 公众号相关 ==========
    
    def add_account(self, name, fakeid=None, nickname=None, alias=None):
        """添加或更新公众号"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO accounts (name, fakeid, nickname, alias)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                fakeid = COALESCE(excluded.fakeid, fakeid),
                nickname = COALESCE(excluded.nickname, nickname),
                alias = COALESCE(excluded.alias, alias)
        ''', (name, fakeid, nickname, alias))
        
        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        return account_id
    
    def get_account_by_name(self, name):
        """根据名称获取公众号"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_accounts(self):
        """获取所有公众号"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY last_scraped_at DESC')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def update_account_stats(self, account_id, total_articles):
        """更新公众号统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts 
            SET last_scraped_at = CURRENT_TIMESTAMP, total_articles = ?
            WHERE id = ?
        ''', (total_articles, account_id))
        conn.commit()
        conn.close()
    
    # ========== 文章相关 ==========
    
    def add_article(self, account_id, title, link, publish_date, content=None):
        """添加文章，如果存在则返回ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO articles (account_id, title, link, publish_date, content) VALUES (?, ?, ?, ?, ?)",
                (account_id, title, link, publish_date, content)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM articles WHERE link = ?", (link,))
            result = cursor.fetchone()
            if result:
                # 如果提供了content，更新它
                if content:
                    cursor.execute("UPDATE articles SET content = ? WHERE id = ?", (content, result[0]))
                    conn.commit()
                return result[0]
            return None

    def update_article_content(self, article_id, content):
        """更新文章内容"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE articles SET content = ? WHERE id = ?", (content, article_id))
        conn.commit()
        conn.close()

    def search_articles(self, query):
        """搜索文章（标题或内容）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        search_query = f"%{query}%"
        cursor.execute('''
            SELECT a.id, a.title, a.link, a.publish_date, a.downloaded, a.local_path, acc.name 
            FROM articles a 
            JOIN accounts acc ON a.account_id = acc.id 
            WHERE a.title LIKE ? OR a.content LIKE ? 
            ORDER BY a.publish_date DESC
        ''', (search_query, search_query))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_all_articles_with_account(self):
        """获取所有文章及其公众号信息（用于导出）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, acc.name, a.title, a.publish_date, a.status, a.link, a.local_path, a.content
            FROM articles a 
            JOIN accounts acc ON a.account_id = acc.id 
            ORDER BY a.publish_date DESC
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def mark_article_downloaded(self, article_id, filepath, image_count=0):
        """标记文章为已下载"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles 
            SET downloaded = 1, local_path = ?, image_count = ?, status = 'completed'
            WHERE id = ?
        ''', (filepath, image_count, article_id))
        conn.commit()
        conn.close()
    
    def mark_article_failed(self, article_id, error_message):
        """标记文章下载失败"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles 
            SET status = 'failed', error_message = ?, retry_count = retry_count + 1
            WHERE id = ?
        ''', (error_message, article_id))
        conn.commit()
        conn.close()
    
    def is_downloaded(self, link):
        """检查文章是否已下载"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT downloaded FROM articles WHERE link = ?", (link,))
        result = cursor.fetchone()
        conn.close()
        return result and result[0]
    
    def get_article_by_link(self, link):
        """通过链接获取文章"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE link = ?", (link,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_articles_by_account(self, account_id):
        """获取公众号的所有文章"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE account_id = ? ORDER BY publish_date DESC", (account_id,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    # ========== 频率限制相关 ==========
    
    # ========== 频率限制相关 ==========
    
    def record_rate_limit(self, account_name=None, error_code='200013'):
        """记录频率限制"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 估计30分钟后解除
        cursor.execute('''
            INSERT INTO rate_limits (account_name, reset_time)
            VALUES (?, datetime('now', '+30 minutes'))
        ''', (account_name,))
        
        conn.commit()
        conn.close()
    
    def get_latest_rate_limit(self):
        """获取最近的频率限制记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM rate_limits 
            ORDER BY triggered_at DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        return result
    
    def is_rate_limited(self):
        """检查当前是否处于频率限制中"""
        limit = self.get_latest_rate_limit()
        if not limit:
            return False
        
        # limit[3] 是 reset_time (id, account_name, triggered_at, reset_time)
        if limit[3]:
            reset_time = datetime.fromisoformat(limit[3])
            return datetime.now() < reset_time
        return False
    
    # ========== 任务相关 ==========
    
    def create_task(self, account_name, task_type='single', pages=1):
        """创建任务"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (account_name, type, pages, status, create_time)
            VALUES (?, ?, ?, 'running', CURRENT_TIMESTAMP)
        ''', (account_name, task_type, pages))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id
    
    def update_task_progress(self, task_id, total_articles, downloaded_articles, failed_articles):
        """更新任务进度"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks 
            SET total_articles = ?, downloaded_count = ?, failed_count = ?
            WHERE id = ?
        ''', (total_articles, downloaded_articles, failed_articles, task_id))
        conn.commit()
        conn.close()
    
    def complete_task(self, task_id, status='completed', error_message=None):
        """完成任务"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks 
            SET status = ?, end_time = CURRENT_TIMESTAMP, error_message = ?
            WHERE id = ?
        ''', (status, error_message, task_id))
        conn.commit()
        conn.close()
    
    def get_task_stats(self, task_id):
        """获取任务统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    # ========== 高级搜索和数据管理 ==========
    
    def search_articles_advanced(self, query='', account_id=None, date_from=None, date_to=None, sort_by='date', order='desc', is_favorite=None, is_read=None, limit=None, offset=0):
        """高级搜索文章"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        # 关键字搜索
        if query:
            search_query = f"%{query}%"
            conditions.append("(a.title LIKE ? OR a.content LIKE ?)")
            params.extend([search_query, search_query])
        
        # 公众号过滤
        if account_id:
            conditions.append("a.account_id = ?")
            params.append(account_id)
        
        # 日期范围
        if date_from:
            conditions.append("a.publish_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("a.publish_date <= ?")
            params.append(date_to)
        
        # 收藏状态
        if is_favorite is not None:
            conditions.append("a.is_favorite = ?")
            params.append(1 if is_favorite else 0)
        
        # 已读状态
        if is_read is not None:
            conditions.append("a.is_read = ?")
            params.append(1 if is_read else 0)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 排序
        if sort_by == 'date':
            order_clause = f"a.publish_date {order.upper()}"
        else:
            order_clause = "a.publish_date DESC"
        
        sql = f'''
            SELECT a.id, a.title, a.link, a.publish_date, a.downloaded, a.local_path, acc.name, a.is_favorite, a.is_read, a.tags
            FROM articles a 
            JOIN accounts acc ON a.account_id = acc.id 
            WHERE {where_clause}
            ORDER BY {order_clause}
        '''
        
        if limit:
            sql += f" LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def toggle_favorite(self, article_id):
        """切换收藏状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE articles SET is_favorite = NOT is_favorite WHERE id = ?", (article_id,))
        conn.commit()
        conn.close()
    
    def toggle_read(self, article_id):
        """切换已读状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE articles SET is_read = NOT is_read WHERE id = ?", (article_id,))
        conn.commit()
        conn.close()
    
    def update_tags(self, article_id, tags):
        """更新文章标签"""
        conn = self.get_connection()
        cursor = conn.cursor()
        tags_str = ','.join(tags) if isinstance(tags, list) else tags
        cursor.execute("UPDATE articles SET tags = ? WHERE id = ?", (tags_str, article_id))
        conn.commit()
        conn.close()
    
    def batch_delete_articles(self, article_ids):
        """批量删除文章"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(article_ids))
        cursor.execute(f"DELETE FROM articles WHERE id IN ({placeholders})", article_ids)
        conn.commit()
        conn.close()
    
    def batch_mark_read(self, article_ids, is_read=True):
        """批量标记已读/未读"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(article_ids))
        cursor.execute(f"UPDATE articles SET is_read = ? WHERE id IN ({placeholders})", [1 if is_read else 0] + article_ids)
        conn.commit()
        conn.close()

