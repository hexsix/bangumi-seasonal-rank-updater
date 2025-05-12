use axum::{
    routing::get,
    Json, Router,
    extract::Query,
};
use serde::Deserialize;

mod scrapying;

#[derive(Deserialize)]
struct SeasonQuery {
    season: String,
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(root))
        .route("/available_seasons", get(available_seasons))
        .route("/seasonal_bangumi_list", get(seasonal_bangumi_list_handler));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn root() -> &'static str {
    "Hello, World!"
}

async fn available_seasons() -> Json<Vec<String>> {
    Json(vec!["202501".to_string(), "202504".to_string()])
}

async fn seasonal_bangumi_list_handler(Query(query): Query<SeasonQuery>) -> Json<Vec<String>> {
    scrapying::youranimes_tw::get_seasonal_bangumi_list(query.season).await
}
