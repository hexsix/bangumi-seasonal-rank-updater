use crate::bgm::models::{PagedEpisode, PagedIndexSubject, Subject};
use anyhow::Result;
use dotenvy::dotenv;
use reqwest::header::HeaderMap;
use reqwest::{header, Client};
use serde_json;
use std::env;
use tracing::info;

/*
get /v0/episodes
subject_id: i32
type: i32
limit: i32
offset: i32
*/
pub async fn get_episodes(
    subject_id: i32,
    episode_type: i32,
    limit: i32,
    offset: i32,
) -> Result<PagedEpisode> {
    info!("Getting episodes for subject_id: {}", subject_id);
    dotenv().ok();
    let api_key = env::var("BGM_API_KEY").expect("BGM_API_KEY is not set");
    let client = Client::new();
    let url = format!(
        "https://api.bgm.tv/v0/episodes?subject_id={}&type={}&limit={}&offset={}",
        subject_id, episode_type, limit, offset
    );
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    headers.insert(
        header::AUTHORIZATION,
        format!("Bearer {}", api_key).parse().unwrap(),
    );
    let response = client.get(url).headers(headers).send().await?;
    let body = response.json::<PagedEpisode>().await?;
    Ok(body)
}

/*
get /v0/indices/{index_id}/subjects
type: 2
limit: i32
offset: i32
*/
pub async fn get_index(
    index_id: i32,
    subject_type: i32,
    limit: i32,
    offset: i32,
) -> Result<PagedIndexSubject> {
    info!("Getting index for index_id: {}", index_id);
    dotenv().ok();
    let api_key = env::var("BGM_API_KEY").expect("BGM_API_KEY is not set");
    let client = Client::new();
    let url = format!(
        "https://api.bgm.tv/v0/indices/{}/subjects?type={}&limit={}&offset={}",
        index_id, subject_type, limit, offset
    );
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    headers.insert(
        header::AUTHORIZATION,
        format!("Bearer {}", api_key).parse().unwrap(),
    );
    let response = client.get(url).headers(headers).send().await?;
    let body = response.json::<PagedIndexSubject>().await?;
    Ok(body)
}

/*
get /v0/subjects/{subject_id}
*/
pub async fn get_subject(id: i32) -> Result<Subject> {
    info!("Getting subject for id: {}", id);
    dotenv().ok();
    let api_key = env::var("BGM_API_KEY").expect("BGM_API_KEY is not set");
    let client = Client::new();
    let url = format!("https://api.bgm.tv/v0/subjects/{}", id);
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    headers.insert(
        header::AUTHORIZATION,
        format!("Bearer {}", api_key).parse().unwrap(),
    );
    let response = client.get(url).headers(headers).send().await?;

    let status = response.status();

    if !status.is_success() {
        return Err(anyhow::anyhow!(format!(
            "BGM API returned status: {}",
            status
        )));
    }

    let text = response.text().await?;

    let body: Subject =
        serde_json::from_str(&text).map_err(|e| anyhow::anyhow!("Failed to parse JSON: {}", e))?;
    Ok(body)
}
