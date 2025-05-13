use axum::{http::HeaderMap, Json};
use reqwest::{self, header};

pub async fn get_seasonal_bangumi_list(season: String) -> Json<Vec<String>> {
    let client = reqwest::Client::new();
    let mut headers = HeaderMap::new();
    headers.insert(header::USER_AGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".parse().unwrap());
    let res = client.get(format!("https://youranimes.tw/bangumi/{}", season)).headers(headers).send().await.unwrap();
    println!("{:?}", res.text().await.unwrap());
    Json(vec!["その着せ替え人形は恋をする Season 2".to_string(), "ダンダダン 第2期".to_string(), "怪獣8号 第2期".to_string()])
}
