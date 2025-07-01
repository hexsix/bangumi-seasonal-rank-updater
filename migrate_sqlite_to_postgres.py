#!/usr/bin/env python3
"""
从SQLite迁移数据到PostgreSQL的脚本
"""

import sqlite3
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import config
from app.services.db.schemas import Index, Subject, YucWiki


def migrate_data(sqlite_db_path: str):
    """从SQLite数据库迁移数据到PostgreSQL"""

    # 检查SQLite文件是否存在
    if not Path(sqlite_db_path).exists():
        logger.error(f"SQLite数据库文件不存在: {sqlite_db_path}")
        return False

    # 连接PostgreSQL
    pg_engine = create_engine(config.db_url)
    pg_session = Session(pg_engine)

    try:
        # 连接SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row  # 让查询结果可以通过列名访问

        logger.info("开始数据迁移...")

        # 迁移Index表
        logger.info("迁移Index表...")
        sqlite_cursor = sqlite_conn.execute("SELECT * FROM `index`")
        index_count = 0
        for row in sqlite_cursor:
            index = Index(
                season_id=row["season_id"],
                index_id=row["index_id"],
                subject_ids=row["subject_ids"],
            )
            pg_session.merge(index)
            index_count += 1

        # 迁移Subject表
        logger.info("迁移Subject表...")
        sqlite_cursor = sqlite_conn.execute("SELECT * FROM subject")
        subject_count = 0
        for row in sqlite_cursor:
            subject = Subject(
                id=row["id"],
                name=row["name"],
                name_cn=row["name_cn"],
                images_grid=row["images_grid"],
                images_large=row["images_large"],
                rank=row["rank"],
                score=row["score"],
                collection_total=row["collection_total"],
                average_comment=row["average_comment"],
                drop_rate=row["drop_rate"],
                air_weekday=row["air_weekday"],
                meta_tags=row["meta_tags"],
                updated_at=row["updated_at"],
            )
            pg_session.merge(subject)
            subject_count += 1

        # 迁移YucWiki表
        logger.info("迁移YucWiki表...")
        sqlite_cursor = sqlite_conn.execute("SELECT * FROM yucwiki")
        yucwiki_count = 0
        for row in sqlite_cursor:
            yucwiki = YucWiki(
                id=row["id"], jp_title=row["jp_title"], subject_id=row["subject_id"]
            )
            pg_session.merge(yucwiki)
            yucwiki_count += 1

        # 提交事务
        pg_session.commit()

        logger.info("数据迁移完成！")
        logger.info(f"- Index记录: {index_count}")
        logger.info(f"- Subject记录: {subject_count}")
        logger.info(f"- YucWiki记录: {yucwiki_count}")

        return True

    except Exception as e:
        logger.error(f"迁移失败: {e}")
        pg_session.rollback()
        return False

    finally:
        sqlite_conn.close()
        pg_session.close()
        pg_engine.dispose()


def main():
    """主函数"""
    import sys

    if len(sys.argv) != 2:
        print("用法: python migrate_sqlite_to_postgres.py <sqlite_db_path>")
        print("示例: python migrate_sqlite_to_postgres.py data/rank.db")
        sys.exit(1)

    sqlite_db_path = sys.argv[1]

    logger.info(f"开始从 {sqlite_db_path} 迁移数据到PostgreSQL")
    logger.info(f"目标数据库: {config.db_url_masked()}")

    if migrate_data(sqlite_db_path):
        logger.info("✅ 数据迁移成功完成！")
    else:
        logger.error("❌ 数据迁移失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
