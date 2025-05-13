use axum::{
    routing::{get, post},
    Json, Router,
    extract::{Query, State},
    debug_handler,
};
use diesel_async::{
    pooled_connection::AsyncDieselConnectionManager, AsyncPgConnection,
};
use serde::{Deserialize, Serialize};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod scrapying;
mod db;
mod bgm;
use db::models::*;

type Pool = bb8::Pool<AsyncDieselConnectionManager<AsyncPgConnection>>;

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| format!("{}=debug", env!("CARGO_CRATE_NAME")).into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let db_url = std::env::var("DATABASE_URL").expect("DATABASE_URL is not set");

    let config = AsyncDieselConnectionManager::<diesel_async::AsyncPgConnection>::new(db_url);
    let pool = bb8::Pool::builder().build(config).await.unwrap();
    
    let app = Router::new()
        .route("/", get(root))
        .route("/available_seasons", get(available_seasons))
        .route("/seasonal_bangumi_list", get(seasonal_bangumi_list_handler))
        .route("/index/create", post(create_bgm_tv_index_handler))
        .route("/index/detail", get(index_detail_handler))
        .route("/subject/detail", get(subject_detail_handler))
        .with_state(pool);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn root() -> &'static str {
    "Hello, World!"
}

async fn available_seasons() -> Json<Vec<String>> {
    Json(vec!["202501".to_string(), "202504".to_string()])
}

#[derive(Deserialize)]
struct SeasonQuery {
    season: String,
}

async fn seasonal_bangumi_list_handler(Query(query): Query<SeasonQuery>) -> Json<Vec<String>> {
    scrapying::youranimes_tw::get_seasonal_bangumi_list(query.season).await
}

#[derive(Serialize, Deserialize)]
struct BgmTvIndexRequest {
    id: i32,
    season_name: String,
    verified: bool,
}

#[debug_handler]
async fn create_bgm_tv_index_handler(
    State(pool): State<Pool>,
    Json(json): Json<BgmTvIndexRequest>) -> Result<Json<BgmTvIndexRequest>, (axum::http::StatusCode, String)> {
    match db::create_bgm_tv_index(&pool, json.id, &json.season_name, json.verified).await {
        Ok(_) => Ok(Json(json)),
        Err(e) => Err((axum::http::StatusCode::INTERNAL_SERVER_ERROR, e.to_string())),
    }
}

#[derive(Deserialize)]
struct IndexDetailQuery {
    index_id: i32,
}

async fn index_detail_handler(Query(query): Query<IndexDetailQuery>) -> Result<Json<Vec<String>>, (axum::http::StatusCode, String)> {
    match bgm::get_bgm_tv_index_subject_ids(query.index_id).await {
        Ok(subject_ids) => Ok(Json(subject_ids.iter().map(|v| v.to_string()).collect())),
        Err(e) => Err((axum::http::StatusCode::INTERNAL_SERVER_ERROR, e.to_string())),
    }
}

#[derive(Deserialize)]
struct SubjectDetailQuery {
    subject_id: i32,
}

async fn subject_detail_handler(Query(query): Query<SubjectDetailQuery>) -> Result<Json<BgmTvSubject>, (axum::http::StatusCode, String)> {
    match bgm::get_bgm_tv_subject_detail(query.subject_id, "202501".to_string()).await {
        Ok(subject) => Ok(subject),
        Err(e) => Err((axum::http::StatusCode::INTERNAL_SERVER_ERROR, e.to_string())),
    }
}
