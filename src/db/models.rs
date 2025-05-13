use diesel::{Queryable, Selectable};
use std::time::SystemTime;
use crate::db::schema::*;

#[derive(serde::Serialize, serde::Deserialize, Queryable, Selectable,)]
#[diesel(table_name = youranime_tw)]
pub struct YourAnimeTw {
    pub id: i32,
    pub season_name: String,
    pub name: String,
    pub subject_id: Option<i32>,
    pub created_at: SystemTime,
    pub updated_at: SystemTime,
}

#[derive(serde::Serialize, serde::Deserialize, Queryable, Selectable,)]
#[diesel(table_name = bgm_tv_index)]
pub struct BgmTvIndex {
    pub id: i32,
    pub season_name: String,
    pub subject_ids: Option<Vec<String>>,
    pub verified: bool,
    pub created_at: SystemTime,
    pub updated_at: SystemTime,
}

#[derive(serde::Serialize, serde::Deserialize, Queryable, Selectable,)]
#[diesel(table_name = bgm_tv_subject)]
pub struct BgmTvSubject {
    pub id: i32,
    pub season_name: String,
    pub name: String,
    pub name_cn: String,
    pub date: String,
    pub images_grid: String,
    pub images_large: String,
    pub air_weekday: String,
    pub rank: i32,
    pub score: f32,
    pub rating_count: i32,
    pub collection_on_hold: i32,
    pub collection_dropped: i32,
    pub collection_wish: i32,
    pub collection_collect: i32,
    pub collection_doing: i32,
    pub meta_tags: Vec<String>,
    pub nsfw: bool,
    pub created_at: SystemTime,
    pub updated_at: SystemTime,
}
