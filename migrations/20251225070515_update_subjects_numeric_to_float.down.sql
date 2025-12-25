-- Add down migration script here
ALTER TABLE subjects
    ALTER COLUMN score TYPE DECIMAL(4, 2),
    ALTER COLUMN average_comment TYPE DECIMAL(4, 2),
    ALTER COLUMN drop_rate TYPE DECIMAL(4, 2);
