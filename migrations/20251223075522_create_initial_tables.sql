-- 创建 seasons 表（季度信息）
CREATE TABLE seasons (
    season_id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    season VARCHAR(10) NOT NULL,
    bangumi_index_id INTEGER NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_seasons_year_season ON seasons(year, season);
CREATE INDEX idx_seasons_bangumi_index ON seasons(bangumi_index_id);

-- 创建 subjects 表（番剧详细信息）
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    name_cn VARCHAR(255),
    images_grid VARCHAR(500),
    images_large VARCHAR(500),
    rank INTEGER,
    score DECIMAL(4, 2),
    collection_total INTEGER,
    average_comment DECIMAL(4, 2),
    drop_rate DECIMAL(5, 2),
    air_weekday VARCHAR(20),
    meta_tags TEXT[],
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subjects_rank ON subjects(rank);
CREATE INDEX idx_subjects_score ON subjects(score DESC);

-- 创建 season_subjects 表（季度-番剧关联）
CREATE TABLE season_subjects (
    season_id INTEGER NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    display_order INTEGER,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (season_id, subject_id)
);

CREATE INDEX idx_season_subjects_season ON season_subjects(season_id);
CREATE INDEX idx_season_subjects_subject ON season_subjects(subject_id);
