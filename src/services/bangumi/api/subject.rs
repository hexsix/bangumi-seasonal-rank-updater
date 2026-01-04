use crate::services::bangumi::{BangumiClient, schemas::*};
use anyhow::{Context, Result};

impl BangumiClient {
    pub async fn get_subject(&self, subject_id: i32) -> Result<Subject> {
        /*
            获取条目详细信息

        GET /v0/subjects/{subject_id}

        Args:
            subject_id: 条目ID

        Returns:
            Subject: 条目详细信息
        */
        let url = self
            .base_url
            .join(&format!("/v0/subjects/{}", subject_id))
            .unwrap();

        let response = self
            .client
            .get(url.as_str())
            .send()
            .await
            .context("发送请求失败")?;

        if !response.status().is_success() {
            anyhow::bail!("API 返回错误状态码: {}, URL: {}", response.status(), url);
        }

        let subject = response
            .json::<Subject>()
            .await
            .context("解析响应 JSON 失败")?;

        Ok(subject)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_get_subject() {
        let client = BangumiClient::new();
        let subject = client.get_subject(400602).await.unwrap();

        assert_eq!(subject.id, 400602);
        assert_eq!(subject.name_cn, Some("葬送的芙莉莲".to_string()));
        assert!(subject.rating.is_some());
    }

    #[tokio::test]
    async fn test_bad_subject_not_found() {
        let client = BangumiClient::new();
        let subject = client.get_subject(999999999).await;

        assert!(subject.is_err());
    }

    #[tokio::test]
    async fn test_get_subject_redirect() {
        let client = BangumiClient::new();
        let subject = client.get_subject(141079).await.unwrap();

        assert_eq!(subject.id, 104906);
        assert_eq!(subject.name_cn, Some("境界触发者".to_string()));
        assert!(subject.rating.is_some());
    }
}
