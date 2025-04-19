# backend/database/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path # <--- 需要导入 Path
import logging          # <--- 需要导入 logging

# --- 计算数据库文件的绝对路径 ---

# 1. 获取 database.py 文件所在的目录 (code/backend/database)
CURRENT_DIR = Path(__file__).resolve().parent

# 2. 定义数据库文件名
DB_FILENAME = "masumi.db"

# 3. 构造数据库文件的绝对路径 (它和 database.py 在同一个目录下)
DB_ABSOLUTE_PATH = CURRENT_DIR / DB_FILENAME

# 4. 构造 SQLite 的 DATABASE_URL (使用 resolve() 确保是绝对路径)
DATABASE_URL = f"sqlite:///{DB_ABSOLUTE_PATH.resolve()}"

# 打印日志确认最终使用的路径 (方便调试)
logging.basicConfig(level=logging.INFO) # 确保 logging 已配置
logging.info(f"Database configured at absolute path: {DATABASE_URL}")

# --- SQLAlchemy 设置保持不变 ---

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} # Needed for SQLite with FastAPI/threading
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for ORM models
Base = declarative_base()