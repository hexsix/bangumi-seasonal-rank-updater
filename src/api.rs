use crate::{
    bgm::{get_bgm_tv_index_subject_ids, get_bgm_tv_subject_detail},
    AppState,
};
use anyhow::Result;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use redis::aio::MultiplexedConnection;
use serde::{Deserialize, Serialize};
use std::time::SystemTime;
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeasonData {
    pub season_id: i32,
    pub subjects: Vec<Subject>,
    pub last_updated: SystemTime,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorDetail {
    pub code: i32,
    pub message: String,
}

pub async fn root() -> &'static str {
    "Hello, World!"
}

#[axum::debug_handler]
pub async fn update_all_seasons(State(state): State<AppState>) -> impl IntoResponse {
    info!("Updating all seasons");
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(conn) => conn,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(
                    serde_json::to_value(ErrorDetail {
                        code: 500,
                        message: format!("Redis connection error: {}", e),
                    })
                    .unwrap(),
                ),
            )
        }
    };

    let seasons = vec![(202501, 67220), (202504, 74306)];

    for season in seasons {
        if let Err(e) = update_season(season.0, season.1, &mut conn).await {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(
                    serde_json::to_value(ErrorDetail {
                        code: 500,
                        message: format!("Update season error: {}", e),
                    })
                    .unwrap(),
                ),
            );
        }
    }

    (
        StatusCode::OK,
        Json(
            serde_json::to_value(ErrorDetail {
                code: 200,
                message: "All seasons updated successfully".to_string(),
            })
            .unwrap(),
        ),
    )
}

pub async fn update_season(
    season_id: i32,
    index_id: i32,
    conn: &mut MultiplexedConnection,
) -> Result<()> {
    let subject_ids = get_bgm_tv_index_subject_ids(index_id).await?;
    let mut subjects = Vec::new();
    for subject_id in subject_ids {
        let subject = get_bgm_tv_subject_detail(subject_id).await?;
        let subject = serde_json::from_value(subject).unwrap();
        subjects.push(subject);
    }
    let data = SeasonData {
        season_id,
        subjects,
        last_updated: SystemTime::now(),
    };
    redis::cmd("SET")
        .arg(format!("season:{}", season_id))
        .arg(serde_json::to_string(&data).unwrap())
        .exec_async(conn)
        .await?;
    Ok(())
}

#[axum::debug_handler]
pub async fn get_season(
    Path(season_id): Path<i32>,
    State(state): State<AppState>,
) -> impl IntoResponse {
    info!("Getting season: {}", season_id);
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(conn) => conn,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(
                    serde_json::to_value(ErrorDetail {
                        code: 500,
                        message: format!("Redis connection error: {}", e),
                    })
                    .unwrap(),
                ),
            )
        }
    };

    let result: Result<Option<String>, redis::RedisError> = redis::cmd("GET")
        .arg(format!("season:{}", season_id))
        .query_async(&mut conn)
        .await;

    match result {
        Ok(Some(data)) => match serde_json::from_str::<SeasonData>(&data) {
            Ok(season_data) => (
                StatusCode::OK,
                Json(serde_json::to_value(season_data).unwrap()),
            ),
            Err(e) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(
                    serde_json::to_value(ErrorDetail {
                        code: 500,
                        message: format!("Failed to parse season data: {}", e),
                    })
                    .unwrap(),
                ),
            ),
        },
        Ok(None) => (
            StatusCode::NOT_FOUND,
            Json(
                serde_json::to_value(ErrorDetail {
                    code: 404,
                    message: format!("Season {} not found", season_id),
                })
                .unwrap(),
            ),
        ),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(
                serde_json::to_value(ErrorDetail {
                    code: 500,
                    message: format!("Redis query error: {}", e),
                })
                .unwrap(),
            ),
        ),
    }
}

#[axum::debug_handler]
pub async fn available_seasons(State(state): State<AppState>) -> impl IntoResponse {
    info!("Getting available seasons");
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(conn) => conn,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(
                    serde_json::to_value(ErrorDetail {
                        code: 500,
                        message: format!("Redis connection error: {}", e),
                    })
                    .unwrap(),
                ),
            )
        }
    };

    let result: Result<Vec<String>, redis::RedisError> = redis::cmd("KEYS")
        .arg("season:*")
        .query_async(&mut conn)
        .await;

    match result {
        Ok(seasons) => {
            let mut seasons: Vec<i32> = seasons
                .iter()
                .map(|s| s.split(":").nth(1).unwrap().parse::<i32>().unwrap())
                .collect();
            seasons.sort_by(|a, b| b.cmp(a));
            (StatusCode::OK, Json(serde_json::to_value(seasons).unwrap()))
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(
                serde_json::to_value(ErrorDetail {
                    code: 500,
                    message: format!("Redis query error: {}", e),
                })
                .unwrap(),
            ),
        ),
    }
}
