-- Your SQL goes here
CREATE TABLE "bgm_tv_index"(
    "id" SERIAL PRIMARY KEY,
    "season_name" TEXT NOT NULL,
    "subject_ids" TEXT[],
    "verified" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "bgm_tv_subject"(
    "id" SERIAL PRIMARY KEY,
    "season_name" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "name_cn" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "images_grid" TEXT NOT NULL,
    "images_large" TEXT NOT NULL,
    "air_weekday" TEXT NOT NULL,
    "rank" INTEGER NOT NULL,
    "score" FLOAT NOT NULL,
    "rating_count" INTEGER NOT NULL,
    "collection_on_hold" INTEGER NOT NULL,
    "collection_dropped" INTEGER NOT NULL,
    "collection_wish" INTEGER NOT NULL,
    "collection_collect" INTEGER NOT NULL,
    "collection_doing" INTEGER NOT NULL,
    "meta_tags" TEXT[] NOT NULL,
    "nsfw" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "youranime_tw"(
    "id" SERIAL PRIMARY KEY,
    "season_name" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "subject_id" INTEGER REFERENCES "bgm_tv_subject"("id"),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
