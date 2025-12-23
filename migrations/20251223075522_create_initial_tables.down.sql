-- 回滚迁移：删除所有表
-- 注意：删除顺序要与创建顺序相反，先删除有外键依赖的表

DROP TABLE IF EXISTS season_subjects;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS seasons;
