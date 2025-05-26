use diesel::{Queryable, Selectable, Insertable};
use std::time::SystemTime;
use crate::db::schema::*;

#[derive(serde::Serialize, serde::Deserialize, Queryable, Selectable, Debug, Clone)]
#[diesel(table_name = season)]
pub struct Season {
    pub season_id: i32,
    pub index_id: i32,
    pub verified: bool,
}

#[derive(serde::Serialize, serde::Deserialize, Queryable, Selectable, Debug, Clone)]
#[diesel(table_name = subject)]
pub struct Subject {
    pub subject_id: i32,
    pub name: String,
    pub name_cn: String,
    pub images_grid: String,
    pub images_large: String,
    pub rank: i32,
    pub score: f32,
    pub collection_total: i32,
    pub average_comment: f32,
    pub drop_rate: f32,
    pub air_weekday: String,
    pub meta_tags: Vec<String>,
}

#[derive(serde::Serialize, serde::Deserialize, Queryable, Selectable, Debug, Clone)]
#[diesel(table_name = subject_season)]
pub struct SubjectSeason {
    pub subject_season_id: i32,
    pub subject_id: Option<i32>,
    pub season_id: Option<i32>,
    pub updated_at: SystemTime,
}
