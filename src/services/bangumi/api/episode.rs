use crate::services::bangumi::{BangumiClient, schemas::*};
use anyhow::Result;

impl BangumiClient {
    pub async fn get_episodes(
        &self,
        subject_id: i32,
        episode_type: i32,
        limit: i32,
        offset: i32,
    ) -> Result<PagedEpisode> {
        /*
            获取剧集信息

        GET /v0/episodes

        Args:
            subject_id: 条目ID
            episode_type: 剧集类型 (本篇=0 特别篇=1 OP=2 ED=3 预告/宣传/广告=4 MAD=5 其他=6)
            limit: 每页数量
            offset: 偏移量

        Returns:
            PagedEpisode: 分页剧集数据

        Raises:
            httpx.HTTPStatusError: 当API返回错误状态码时
            ValueError: 当响应数据解析失败或重定向次数过多时
        */
        todo!()
    }
}
