use axum::{Json, Router, routing::get};
use serde::Serialize;

#[derive(Serialize)]
struct HealthResponse {
    status: String,
}

async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
    })
}

fn app() -> Router {
    Router::new().route("/health", get(health_check))
}

#[tokio::main]
async fn main() {
    let addr = "0.0.0.0:3000";

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("无法绑定端口");

    axum::serve(listener, app()).await.expect("服务器运行错误");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::Body,
        http::{Request, StatusCode},
    };
    use tower::ServiceExt;

    #[tokio::test]
    async fn test_health_check() {
        let app = app();

        let request = Request::builder()
            .uri("/health")
            .body(Body::empty())
            .unwrap();

        let response = app.oneshot(request).await.unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        // TODO: assert response body == {"status": "ok"}
    }
}
