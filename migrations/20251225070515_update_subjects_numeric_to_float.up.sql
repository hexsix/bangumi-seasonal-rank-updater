-- Add up migration script here
ALTER TABLE subjects
    ALTER COLUMN score TYPE DOUBLE PRECISION,
    ALTER COLUMN average_comment TYPE DOUBLE PRECISION,
    ALTER COLUMN drop_rate TYPE DOUBLE PRECISION;
