use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize, Clone, Copy)]
pub struct Collection {
    pub wish: i32,
    pub collect: i32,
    pub doing: i32,
    pub on_hold: i32,
    pub dropped: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Episode {
    pub id: i32,
    pub episode_type: i32, // 本篇 = 0 特别篇 = 1 OP = 2 ED = 3 预告/宣传/广告 = 4 MAD = 5 其他 = 6
    pub name: String,
    pub name_cn: String,
    pub sort: f32, // 同类条目的排序和集数
    pub ep: f32,   // 条目内的集数, 从1开始。非本篇剧集的此字段无意义
    pub airdate: String,
    pub comment: i32,
    pub duration: String,
    pub desc: String, // 简介
    pub disc: i32,    // 音乐曲目的碟片数
    pub duration_seconds: i32,
    pub subject_id: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorDetail {
    pub title: String,
    pub description: String,
    pub details: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Images {
    pub large: String,
    pub common: String,
    pub medium: String,
    pub small: String,
    pub grid: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IndexSubject {
    pub id: i32,
    #[serde(rename = "type")]
    pub subject_type: i32,
    pub name: String,
    pub images: Images,
    pub infobox: Vec<InfoboxItem>,
    pub date: String,
    pub comment: String,
    pub added_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InfoboxItem {
    pub key: String,
    pub value: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PagedEpisode {
    pub total: i32,
    pub limit: i32,
    pub offset: i32,
    pub data: Vec<Episode>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PagedIndexSubject {
    pub total: i32,
    pub limit: i32,
    pub offset: i32,
    pub data: Vec<IndexSubject>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Rating {
    pub rank: i32,
    pub total: i32,
    pub count: HashMap<i32, i32>,
    pub score: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Subject {
    pub id: i32,
    // 1. book, 2. anime, 3. music, 4. game, 6. real, no 5.
    #[serde(rename = "type")]
    pub subject_type: i32,
    pub name: String,
    pub name_cn: String,
    pub summary: String,
    pub series: bool,
    pub nsfw: bool,
    pub locked: bool,
    // air date in YYYY-MM-DD format
    pub date: String,
    // TV, Web, 欧美剧, DLC...
    pub platform: String,
    pub images: Images,
    pub infobox: Vec<InfoboxItem>,
    pub volumes: i32,
    pub eps: i32,
    pub total_episodes: i32,
    pub rating: Rating,
    pub collection: Collection,
    pub meta_tags: Vec<String>,
    pub tags: Vec<Tag>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Tag {
    pub name: String,
    pub count: i32,
}
