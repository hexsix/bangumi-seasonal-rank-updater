use crate::bgm::models::{PagedEpisode, PagedIndexSubject, Subject};
use reqwest::{header, Client};
use reqwest::header::HeaderMap;
use serde_json;

type Error = Box<dyn std::error::Error + Send + Sync>;

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
) -> Result<PagedEpisode, Error> {
    let client = Client::new();
    let url = format!(
        "https://api.bgm.tv/v0/episodes?subject_id={}&type={}&limit={}&offset={}",
        subject_id, episode_type, limit, offset
    );
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
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
) -> Result<PagedIndexSubject, Error> {
    let client = Client::new();
    let url = format!(
        "https://api.bgm.tv/v0/indices/{}/subjects?type={}&limit={}&offset={}",
        index_id, subject_type, limit, offset
    );
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    let response = client.get(url).headers(headers).send().await?;
    let body = response.json::<PagedIndexSubject>().await?;
    Ok(body)
}

/*
get /v0/subjects/{subject_id}
*/
pub async fn get_subject(id: i32) -> Result<Subject, Error> {
    let client = Client::new();
    let url = format!("https://api.bgm.tv/v0/subjects/{}", id);
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    let response = client.get(url).headers(headers).send().await?;
    
    let status = response.status();
    
    if !status.is_success() {
        return Err(format!("BGM API returned status: {}", status).into());
    }
    
    let text = response.text().await?;
    
    let body: Subject = serde_json::from_str(&text)
        .map_err(|e| format!("Failed to parse JSON: {}", e))?;
    Ok(body)
}
