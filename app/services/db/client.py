import json
import sqlite3
from sqlite3 import Error

from loguru import logger

from app.services.db.schemas import Index, Subject


def create_connection(db_file: str) -> sqlite3.Connection | None:
    """创建数据库连接"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info(f"成功连接到SQLite版本: {sqlite3.sqlite_version}")
        return conn
    except Error as e:
        logger.error(e)
    return conn


def create_index_table(conn: sqlite3.Connection) -> None:
    """创建Index表"""
    sql_create_index_table = """
    CREATE TABLE IF NOT EXISTS rank_index (
        season_id INTEGER PRIMARY KEY,
        index_id INTEGER NOT NULL
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_index_table)
        logger.info("Index表创建成功")
    except Error as e:
        logger.error(e)


def create_subject_table(conn: sqlite3.Connection) -> None:
    """创建Subject表"""
    sql_create_subject_table = """
    CREATE TABLE IF NOT EXISTS rank_subject (
        id INTEGER PRIMARY KEY,
        name TEXT,
        name_cn TEXT,
        images_grid TEXT,
        images_large TEXT,
        rank INTEGER,
        score REAL,
        collection_total INTEGER,
        average_comment REAL,
        drop_rate REAL,
        air_weekday TEXT,
        meta_tags TEXT,
        updated_at TEXT
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_subject_table)
        logger.info("Subject表创建成功")
    except Error as e:
        logger.error(e)


def insert_index(conn: sqlite3.Connection, index: Index) -> int | None:
    """插入Index"""
    sql = """ INSERT INTO rank_index(season_id, index_id)
              VALUES(?,?) """
    cursor = conn.cursor()
    cursor.execute(sql, (index.season_id, index.index_id))
    conn.commit()
    return cursor.lastrowid


def update_index(conn: sqlite3.Connection, index: Index) -> None:
    """更新Index"""
    sql = """ UPDATE rank_index SET index_id = ? WHERE season_id = ? """
    cursor = conn.cursor()
    cursor.execute(sql, (index.index_id, index.season_id))
    conn.commit()
    return None


def delete_index(conn: sqlite3.Connection, season_id: int) -> None:
    """删除Index"""
    sql = """ DELETE FROM rank_index WHERE season_id = ? """
    cursor = conn.cursor()
    cursor.execute(sql, (season_id,))
    conn.commit()
    return None


def get_index(conn: sqlite3.Connection, season_id: int) -> Index | None:
    """获取Index"""
    sql = """ SELECT * FROM rank_index WHERE season_id = ? """
    cursor = conn.cursor()
    cursor.execute(sql, (season_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return Index(season_id=row[0], index_id=row[1])


def get_all_index(conn: sqlite3.Connection) -> list[Index]:
    """获取所有Index"""
    sql = """ SELECT * FROM rank_index """
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return [Index(season_id=row[0], index_id=row[1]) for row in rows]


def get_available_seasons(conn: sqlite3.Connection) -> list[int]:
    """获取所有可用的季节"""
    all_index = get_all_index(conn)
    return [index.season_id for index in all_index]


def _serialize_subject_for_db(subject: Subject) -> tuple:
    """将Subject对象序列化为数据库存储格式（用于插入）"""
    # 序列化meta_tags
    meta_tags_json = None
    if subject.meta_tags is not None:
        meta_tags_json = json.dumps(subject.meta_tags, ensure_ascii=False)

    # 将datetime转换为字符串
    updated_at_str = None
    if subject.updated_at is not None:
        updated_at_str = subject.updated_at.isoformat()

    # 按照INSERT语句的字段顺序返回
    return (
        subject.id,
        subject.name,
        subject.name_cn,
        subject.images_grid,
        subject.images_large,
        subject.rank,
        subject.score,
        subject.collection_total,
        subject.average_comment,
        subject.drop_rate,
        subject.air_weekday,
        meta_tags_json,
        updated_at_str,
    )


def _serialize_subject_for_update(subject: Subject) -> tuple:
    """将Subject对象序列化为数据库更新格式（不包含id，id在WHERE子句中）"""
    # 序列化meta_tags
    meta_tags_json = None
    if subject.meta_tags is not None:
        meta_tags_json = json.dumps(subject.meta_tags, ensure_ascii=False)

    # 将datetime转换为字符串
    updated_at_str = None
    if subject.updated_at is not None:
        updated_at_str = subject.updated_at.isoformat()

    # 按照UPDATE语句的字段顺序返回（不包含id）
    return (
        subject.name,
        subject.name_cn,
        subject.images_grid,
        subject.images_large,
        subject.rank,
        subject.score,
        subject.collection_total,
        subject.average_comment,
        subject.drop_rate,
        subject.air_weekday,
        meta_tags_json,
        updated_at_str,
        subject.id,  # WHERE 子句中的 id
    )


def _deserialize_subject_from_db(row: tuple) -> Subject:
    """将数据库行数据反序列化为Subject对象"""
    if row is None:
        return None

    # 数据库字段顺序：id, name, name_cn, images_grid, images_large, rank, score,
    # collection_total, average_comment, drop_rate, air_weekday, meta_tags, updated_at
    (
        id,
        name,
        name_cn,
        images_grid,
        images_large,
        rank,
        score,
        collection_total,
        average_comment,
        drop_rate,
        air_weekday,
        meta_tags,
        updated_at,
    ) = row

    # 反序列化meta_tags
    if meta_tags is not None:
        try:
            meta_tags = json.loads(meta_tags)
        except json.JSONDecodeError:
            logger.warning(f"无法解析meta_tags JSON: {meta_tags}")
            meta_tags = None

    # 构造Subject对象
    return Subject(
        id=id,
        name=name,
        name_cn=name_cn,
        images_grid=images_grid,
        images_large=images_large,
        rank=rank,
        score=score,
        collection_total=collection_total,
        average_comment=average_comment,
        drop_rate=drop_rate,
        air_weekday=air_weekday,
        meta_tags=meta_tags,
        updated_at=updated_at,
    )


def insert_subject(conn: sqlite3.Connection, subject: Subject) -> int | None:
    """插入Subject"""
    sql = """ INSERT INTO rank_subject(id, name, name_cn, images_grid, images_large, rank, score, collection_total, average_comment, drop_rate, air_weekday, meta_tags, updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) """
    cursor = conn.cursor()
    cursor.execute(sql, _serialize_subject_for_db(subject))
    conn.commit()
    return cursor.lastrowid


def update_subject(conn: sqlite3.Connection, subject: Subject) -> None:
    """更新Subject"""
    sql = """ UPDATE rank_subject SET name = ?, name_cn = ?, images_grid = ?, images_large = ?, rank = ?, score = ?, collection_total = ?, average_comment = ?, drop_rate = ?, air_weekday = ?, meta_tags = ?, updated_at = ? WHERE id = ? """
    cursor = conn.cursor()
    cursor.execute(sql, _serialize_subject_for_update(subject))
    conn.commit()
    return None


def delete_subject(conn: sqlite3.Connection, id: int) -> None:
    """删除Subject"""
    sql = """ DELETE FROM rank_subject WHERE id = ? """
    cursor = conn.cursor()
    cursor.execute(sql, (id,))
    conn.commit()
    return None


def get_subject(conn: sqlite3.Connection, id: int) -> Subject | None:
    """获取Subject"""
    sql = """ SELECT * FROM rank_subject WHERE id = ? """
    cursor = conn.cursor()
    cursor.execute(sql, (id,))
    return _deserialize_subject_from_db(cursor.fetchone())


def get_all_subjects(conn: sqlite3.Connection) -> list[Subject]:
    """获取所有Subject"""
    sql = """ SELECT * FROM rank_subject """
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return [_deserialize_subject_from_db(row) for row in rows if row is not None]


def get_subjects_by_rank_range(
    conn: sqlite3.Connection, min_rank: int, max_rank: int
) -> list[Subject]:
    """根据排名范围获取Subject"""
    sql = """ SELECT * FROM rank_subject WHERE rank BETWEEN ? AND ? ORDER BY rank """
    cursor = conn.cursor()
    cursor.execute(sql, (min_rank, max_rank))
    rows = cursor.fetchall()
    return [_deserialize_subject_from_db(row) for row in rows if row is not None]


# 主程序
if __name__ == "__main__":
    import asyncio

    from app.api.v0.utils import get_subject_detail

    async def main():
        database = "data/rank.db"

        # 创建数据库连接
        conn = create_connection(database)
        if conn is not None:
            # 创建表
            create_index_table(conn)
            create_subject_table(conn)
            subject_id = 398951
            subject_data = await get_subject_detail(subject_id)
            update_subject(conn, subject_data)

            subject = get_subject(conn, subject_id)
            logger.info(subject)

            # 关闭连接
            conn.close()
            logger.info("\n数据库连接已关闭")

    asyncio.run(main())
