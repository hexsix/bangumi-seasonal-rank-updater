use axum::{routing::get, Router};
use dotenvy::dotenv;
use std::env;
use std::sync::Arc;
use tracing::info;

mod api;
mod bgm;
use api::{available_seasons, get_season, root, update_all_seasons};

#[derive(Clone, Debug)]
struct AppState {
    redis_client: Arc<redis::Client>,
}

#[tokio::main]
async fn main() -> redis::RedisResult<()> {
    tracing_subscriber::fmt()
        .json()
        .with_env_filter("bangumi_seasonal_rank_updater=info,warn")
        .init();

    dotenv().ok();

    info!("bangumi seasonal rank updater is starting...");

    let redis_url = env::var("REDIS_URL").expect("REDIS_URL is not set");
    let client = redis::Client::open(redis_url).unwrap();
    let state = AppState {
        redis_client: Arc::new(client),
    };

    let app = Router::new()
        .route("/", get(root))
        .route("/api/v0/seasons", get(available_seasons))
        .route("/api/v0/season/{season_id}", get(get_season))
        .route("/api/v0/update_all/", get(update_all_seasons))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
    Ok(())
}
