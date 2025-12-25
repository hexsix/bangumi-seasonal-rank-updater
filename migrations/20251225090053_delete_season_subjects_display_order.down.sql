-- Add down migration script here
ALTER TABLE season_subjects ADD COLUMN display_order INTEGER;
