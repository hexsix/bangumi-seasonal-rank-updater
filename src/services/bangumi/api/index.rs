use crate::services::bangumi::{BangumiClient, schemas::*};
use anyhow::{Context, Result};

impl BangumiClient {
    pub async fn get_index_subjects(
        &self,
        index_id: i32,
        subject_type: i32,
        limit: i32,
        offset: i32,
    ) -> Result<PagedIndexSubject> {
        /*
        获取索引中的条目

           GET /v0/indices/{index_id}/subjects

           Args:
               index_id: 索引ID
               type: 条目类型 (1=book, 2=anime, 3=music, 4=game, 6=real)
               limit: 每页数量
               offset: 偏移量

           Returns:
               PagedIndexSubject: 分页索引条目数据
        */
        let url = self
            .base_url
            .join(&format!("/v0/indices/{}/subjects", index_id))
            .unwrap();

        let response = self
            .client
            .get(url.as_str())
            .query(&[
                ("type", &subject_type.to_string()),
                ("limit", &limit.to_string()),
                ("offset", &offset.to_string()),
            ])
            .send()
            .await
            .context("发送请求失败")?;

        if !response.status().is_success() {
            anyhow::bail!("API 返回错误状态码: {}, URL: {}", response.status(), url);
        }

        let paged_index_subject = response
            .json::<PagedIndexSubject>()
            .await
            .context("解析响应 JSON 失败")?;

        Ok(paged_index_subject)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_get_index_subjects() {
        let client = BangumiClient::new();
        let paged_index = client.get_index_subjects(85952, 2, 30, 0).await.unwrap();
        assert_eq!(paged_index.total, 60);
        assert_eq!(paged_index.data.len(), 30);
        assert_eq!(
            paged_index.data[0].name,
            Some("TRIGUN STARGAZE".to_string())
        );
    }

    #[tokio::test]
    async fn test_bad_index_not_found() {
        let client = BangumiClient::new();
        let paged_index = client.get_index_subjects(999999999, 2, 30, 0).await;
        assert!(paged_index.is_err());
    }
}
