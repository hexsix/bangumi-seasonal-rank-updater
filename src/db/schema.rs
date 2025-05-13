diesel::table! {
    youranime_tw (id) {
        id -> Int4,
        season_name -> Text,
        name -> Text,
        subject_id -> Nullable<Int4>,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::table! {
    bgm_tv_index (id) {
        id -> Int4,
        season_name -> Text,
        subject_ids -> Nullable<Array<Text>>,
        verified -> Bool,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::table! {
    bgm_tv_subject (id) {
        id -> Int4,
        season_name -> Text,
        name -> Text,
        name_cn -> Text,
        date -> Text,
        images_grid -> Text,
        images_large -> Text,
        air_weekday -> Text,
        rank -> Int4,
        score -> Float4,
        rating_count -> Int4,
        collection_on_hold -> Int4,
        collection_dropped -> Int4,
        collection_wish -> Int4,
        collection_collect -> Int4,
        collection_doing -> Int4,
        meta_tags -> Array<Text>,
        nsfw -> Bool,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::allow_tables_to_appear_in_same_query!(
    youranime_tw, 
    bgm_tv_index, 
    bgm_tv_subject
);
