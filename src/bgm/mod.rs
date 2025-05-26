use self::models::Collection;
use crate::db::models::Subject;
use axum::Json;

pub mod api;
pub mod models;

use api::{get_episodes, get_index, get_subject};
use models::Rating;

type Error = Box<dyn std::error::Error + Send + Sync>;

pub async fn get_bgm_tv_index_subject_ids(index_id: i32) -> Result<Vec<i32>, Error> {
    let mut offset = 0;
    let mut subject_ids = Vec::new();
    loop {
        let index_subjects = get_index(index_id, 2, 50, offset).await?;
        let total = index_subjects.total;
        subject_ids.extend(index_subjects.data.iter().map(|v| v.id));
        if subject_ids.len() >= total as usize {
            break;
        }
        offset += 50;
    }
    Ok(subject_ids)
}

fn get_score(rating: Rating) -> f32 {
    let mut total_count = 0;
    let mut total_score = 0;
    for (score, count) in rating.count {
        total_count += count;
        total_score += score * count;
    }
    total_score as f32 / total_count as f32
}

fn get_total_collection(collection: Collection) -> i32 {
    collection.wish
        + collection.collect
        + collection.doing
        + collection.on_hold
        + collection.dropped
}

async fn get_average_comment(subject_id: i32) -> Result<f32, Error> {
    let mut offset = 0;
    let mut total_comments = 0;
    let mut aired_episodes = 0;
    let now = chrono::Utc::now().date_naive();

    loop {
        let episodes = get_episodes(subject_id, 0, 100, offset).await?;
        let current_batch_size = episodes.data.len();

        for episode in episodes.data {
            // 检查剧集是否已经播出（airdate 不为空且早于或等于当前日期）
            if !episode.airdate.is_empty() {
                if let Ok(air_date) =
                    chrono::NaiveDate::parse_from_str(&episode.airdate, "%Y-%m-%d")
                {
                    if air_date < now {
                        aired_episodes += 1;
                        total_comments += episode.comment;
                    }
                }
            }
        }

        // 如果当前批次的数据少于请求的 limit，说明已经获取完所有数据
        if current_batch_size < 100 {
            break;
        }
        offset += 100;
    }
    if aired_episodes == 0 {
        Ok(0.0)
    } else {
        Ok(total_comments as f32 / aired_episodes as f32)
    }
}

fn get_drop_rate(collection: Collection, collection_total: i32) -> f32 {
    collection.dropped as f32 / collection_total as f32
}

pub async fn get_bgm_tv_subject_detail(subject_id: i32) -> Result<Json<Subject>, Error> {
    let subject = get_subject(subject_id).await?;
    let mut air_weekday = "".to_string();
    for infobox_item in subject.infobox {
        if infobox_item.key == "放送星期" {
            air_weekday = infobox_item.value.as_str().unwrap_or("").to_string();
        }
    }
    let score = get_score(subject.rating.clone());
    let collection_total = get_total_collection(subject.collection);
    let average_comment = get_average_comment(subject_id).await?;
    let drop_rate = get_drop_rate(subject.collection, collection_total);
    let subject_model = Subject {
        subject_id: subject.id,
        name: subject.name,
        name_cn: subject.name_cn,
        images_grid: subject.images.grid,
        images_large: subject.images.large,
        rank: subject.rating.rank,
        score: score,
        collection_total,
        average_comment,
        drop_rate,
        air_weekday,
        meta_tags: subject.meta_tags,
    };
    Ok(Json(subject_model))
}
