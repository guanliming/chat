import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    conn = None
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'chat_app'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE chat_app')
            print("数据库 'chat_app' 创建成功")
        else:
            print("数据库 'chat_app' 已存在")
        
        cursor.close()
    except Exception as e:
        print(f"创建数据库时出错: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_database()
    
    from app import app, db
    with app.app_context():
        db.create_all()
        print("数据库表创建成功")
