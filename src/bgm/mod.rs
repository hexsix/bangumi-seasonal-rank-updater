use axum::{http::HeaderMap, Json};
use reqwest::{header, Client};
use std::time::SystemTime;
use crate::db::models::BgmTvSubject;

type Error = Box<dyn std::error::Error + Send + Sync>;

pub async fn get_bgm_tv_index_subject_ids(index_id: i32) -> Result<Vec<i32>, Error> {
    let client = Client::new();
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    let mut offset = 0;
    let mut subject_ids = Vec::new();
    loop {
        let url = format!("https://api.bgm.tv/v0/indices/{}/subjects?type=2&limit=50&offset={}", index_id, offset);
        let response = client.get(url).headers(headers.clone()).send().await?;
        let body = response.text().await?;
        let json: serde_json::Value = serde_json::from_str(&body)?;
        subject_ids.extend(json["data"].as_array().unwrap().iter().map(|v| v["id"].as_i64().unwrap()));
        let total = json["total"].as_i64().unwrap();
        if subject_ids.len() >= total as usize {
            break;
        }
        offset += 50;
    }
    Ok(subject_ids.iter().map(|v| *v as i32).collect())
}

pub async fn get_bgm_tv_subject_detail(subject_id: i32, season_name: String) -> Result<Json<BgmTvSubject>, Error> {
    let client = Client::new();
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    let url = format!("https://api.bgm.tv/v0/subjects/{}", subject_id);
    let response = client.get(url).headers(headers).send().await?;
    let body = response.text().await?;
    let subject_json: serde_json::Value = serde_json::from_str(&body)?;
    let mut air_weekday = "";
    for v in subject_json["infobox"].as_array().unwrap().iter() {
        if v["key"].as_str().unwrap() == "放送星期" {
            air_weekday = v["value"].as_str().unwrap();
        }
    }
    let subject_model = BgmTvSubject {
        id: subject_id,
        season_name,
        name: subject_json["name"].as_str().unwrap().to_string(),
        name_cn: subject_json["name_cn"].as_str().unwrap().to_string(),
        date: subject_json["date"].as_str().unwrap().to_string(),
        images_grid: subject_json["images"]["grid"].as_str().unwrap().to_string(),
        images_large: subject_json["images"]["large"].as_str().unwrap().to_string(),
        air_weekday: air_weekday.to_string(),
        rank: subject_json["rating"]["rank"].as_i64().unwrap() as i32,
        score: subject_json["rating"]["score"].as_f64().unwrap() as f32,
        rating_count: subject_json["rating"]["total"].as_i64().unwrap() as i32,
        collection_on_hold: subject_json["collection"]["on_hold"].as_i64().unwrap() as i32,
        collection_dropped: subject_json["collection"]["dropped"].as_i64().unwrap() as i32,
        collection_wish: subject_json["collection"]["wish"].as_i64().unwrap() as i32,
        collection_collect: subject_json["collection"]["collect"].as_i64().unwrap() as i32,
        collection_doing: subject_json["collection"]["doing"].as_i64().unwrap() as i32,
        meta_tags: subject_json["meta_tags"].as_array().unwrap().iter().map(|v| v.as_str().unwrap().to_string()).collect(),
        nsfw: subject_json["nsfw"].as_bool().unwrap(),
        created_at: SystemTime::now(),
        updated_at: SystemTime::now(),
    };
    Ok(Json(subject_model))
}
