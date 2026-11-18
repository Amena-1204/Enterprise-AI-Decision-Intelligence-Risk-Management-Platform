-- Migration 001: fix constraints and extend model_versions
-- Run: mysql -u root -p enterprise_ai < backend/app/database/migrations/001_fix_constraints.sql

USE enterprise_ai;

-- ── fraud_predictions: prevent duplicate records per transaction ──────────────
-- Remove duplicates first (keep the most recent row per transaction_id)
DELETE fp1
FROM fraud_predictions fp1
INNER JOIN fraud_predictions fp2
  ON fp1.transaction_id = fp2.transaction_id
 AND fp1.id < fp2.id;

-- Add unique constraint (idempotent via IF NOT EXISTS workaround)
SET @exist := (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'fraud_predictions'
      AND CONSTRAINT_NAME = 'uq_fraud_transaction'
);
SET @sql := IF(@exist = 0,
    'ALTER TABLE fraud_predictions ADD CONSTRAINT uq_fraud_transaction UNIQUE (transaction_id)',
    'SELECT ''uq_fraud_transaction already exists'' AS info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ── model_versions: add mae / rmse columns for regression models ─────────────
ALTER TABLE model_versions
    MODIFY COLUMN accuracy  DECIMAL(10,4) DEFAULT NULL,
    MODIFY COLUMN f1_score  DECIMAL(10,4) DEFAULT NULL,
    MODIFY COLUMN roc_auc   DECIMAL(10,4) DEFAULT NULL;

-- Add mae / rmse only if they don't already exist
SET @col_mae := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'model_versions'
      AND COLUMN_NAME  = 'mae'
);
SET @sql2 := IF(@col_mae = 0,
    'ALTER TABLE model_versions ADD COLUMN mae DECIMAL(12,4) DEFAULT NULL AFTER roc_auc',
    'SELECT ''mae column already exists'' AS info'
);
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

SET @col_rmse := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME   = 'model_versions'
      AND COLUMN_NAME  = 'rmse'
);
SET @sql3 := IF(@col_rmse = 0,
    'ALTER TABLE model_versions ADD COLUMN rmse DECIMAL(12,4) DEFAULT NULL AFTER mae',
    'SELECT ''rmse column already exists'' AS info'
);
PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;
