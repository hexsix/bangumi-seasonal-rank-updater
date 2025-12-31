use crate::services::bangumi::{BangumiClient, schemas::*};
use anyhow::Result;

impl BangumiClient {
    pub async fn get_subject(&self, subject_id: i32, _redirect_count: i32) -> Result<Subject> {
        /*
            获取条目详细信息

        GET /v0/subjects/{subject_id}

        Args:
            subject_id: 条目ID
            _redirect_count: 内部重定向计数，用于防止无限重定向

        Returns:
            Subject: 条目详细信息

        Raises:
            httpx.HTTPStatusError: 当API返回错误状态码时
            ValueError: 当响应数据解析失败或重定向次数过多时
        */
        todo!()
    }
}
