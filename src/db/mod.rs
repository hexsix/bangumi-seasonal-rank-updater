pub mod schema;
pub mod models;

use diesel::prelude::*;
use diesel_async::{
    pooled_connection::AsyncDieselConnectionManager, AsyncPgConnection,
    RunQueryDsl,
};
use axum::{
    extract::{FromRef, FromRequestParts},
    http::{request::Parts, StatusCode},
};
use std::time::SystemTime;
use crate::db::schema::*;

type Pool = bb8::Pool<AsyncDieselConnectionManager<AsyncPgConnection>>;
type Error = Box<dyn std::error::Error + Send + Sync>;

fn internal_error<E>(err: E) -> (StatusCode, String)
where
    E: std::fmt::Display,
{
    (StatusCode::INTERNAL_SERVER_ERROR, err.to_string())
}

#[allow(dead_code)]
struct DatabaseConnection(
    bb8::PooledConnection<'static, AsyncDieselConnectionManager<AsyncPgConnection>>,
);

impl<S> FromRequestParts<S> for DatabaseConnection
where
    S: Send + Sync,
    Pool: FromRef<S>,
{
    type Rejection = (StatusCode, String);

    async fn from_request_parts(_parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let pool = Pool::from_ref(state);

        let conn = pool.get_owned().await.map_err(internal_error)?;

        Ok(Self(conn))
    }
}

pub async fn create_bgm_tv_index(pool: &Pool, index_id: i32, season_name: &str, verified: bool) -> Result<(), Error> {
    let mut conn = pool.get_owned().await.map_err(|e| Box::new(e) as Error)?;
    
    let now = SystemTime::now();
    let index = (
        bgm_tv_index::id.eq(index_id),
        bgm_tv_index::season_name.eq(season_name),
        bgm_tv_index::verified.eq(verified),
        bgm_tv_index::created_at.eq(now),
        bgm_tv_index::updated_at.eq(now),
    );

    diesel::insert_into(bgm_tv_index::table)
        .values(index)
        .execute(&mut conn)
        .await
        .map_err(|e| Box::new(e) as Error)?;

    Ok(())
}

