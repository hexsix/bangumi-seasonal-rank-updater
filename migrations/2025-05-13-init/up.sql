-- Your SQL goes here
CREATE TABLE "season"(
    "season_id" INTEGER PRIMARY KEY,
    "index_id" INTEGER NOT NULL,
    "verified" BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE "subject"(
    "subject_id" INTEGER PRIMARY KEY,
    "name" TEXT NOT NULL,
    "name_cn" TEXT NOT NULL,
    "images_grid" TEXT NOT NULL,
    "images_large" TEXT NOT NULL,
    "rank" INTEGER NOT NULL,
    "score" FLOAT NOT NULL,
    "collection_total" INTEGER NOT NULL,
    "average_comment" FLOAT NOT NULL,
    "drop_rate" FLOAT NOT NULL,
    "air_weekday" TEXT NOT NULL,
    "meta_tags" TEXT[] NOT NULL
);

CREATE TABLE "subject_season"(
    "subject_season_id" SERIAL PRIMARY KEY,
    "subject_id" INTEGER,
    "season_id" INTEGER,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY ("subject_id") REFERENCES "subject"("subject_id"),
    FOREIGN KEY ("season_id") REFERENCES "season"("season_id"),
    UNIQUE ("subject_id", "season_id")
);
