diesel::table! {
    season (season_id) {
        season_id -> Integer,
        index_id -> Integer,
        verified -> Bool,
    }
}

diesel::table! {
    subject (subject_id) {
        subject_id -> Integer,
        name -> Text,
        name_cn -> Text,
        images_grid -> Text,
        images_large -> Text,
        rank -> Integer,
        score -> Float,
        collection_total -> Integer,
        average_comment -> Float,
        drop_rate -> Float,
        air_weekday -> Text,
        meta_tags -> Array<Text>,
    }
}

diesel::table! {
    subject_season (subject_season_id) {
        subject_season_id -> Integer,
        subject_id -> Nullable<Integer>,
        season_id -> Nullable<Integer>,
        updated_at -> Timestamp,
    }
}

diesel::joinable!(subject_season -> season (season_id));
diesel::joinable!(subject_season -> subject (subject_id));

diesel::allow_tables_to_appear_in_same_query!(
    season,
    subject,
    subject_season,
);
