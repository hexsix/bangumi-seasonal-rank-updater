use crate::services::bangumi::{BangumiClient, schemas::*};
use anyhow::Result;

impl BangumiClient {
    pub async fn get_index(
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
               subject_type: 条目类型 (1=book, 2=anime, 3=music, 4=game, 6=real)
               limit: 每页数量
               offset: 偏移量

           Returns:
               PagedIndexSubject: 分页索引条目数据

           Raises:
               httpx.HTTPStatusError: 当API返回错误状态码时
               ValueError: 当响应数据解析失败时
        */
        todo!()
    }
}
