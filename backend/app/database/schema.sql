-- Enterprise AI Decision Intelligence Platform
-- MySQL Schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS enterprise_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE enterprise_ai;

-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    role          ENUM('admin','analyst','viewer') NOT NULL DEFAULT 'viewer',
    is_active     TINYINT(1)   NOT NULL DEFAULT 1,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role  (role)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- CUSTOMERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    external_id          VARCHAR(50)  UNIQUE,
    first_name           VARCHAR(100) NOT NULL,
    last_name            VARCHAR(100) NOT NULL,
    email                VARCHAR(255) NOT NULL UNIQUE,
    phone                VARCHAR(30),
    region               VARCHAR(100),
    country              VARCHAR(100) DEFAULT 'US',
    segment              VARCHAR(50),
    acquisition_channel  VARCHAR(80),
    lifetime_value       DECIMAL(12,2) DEFAULT 0.00,
    total_orders         INT UNSIGNED  DEFAULT 0,
    last_purchase_date   DATE,
    account_age_days     INT UNSIGNED  DEFAULT 0,
    is_active            TINYINT(1)    NOT NULL DEFAULT 1,
    created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customers_region  (region),
    INDEX idx_customers_segment (segment),
    INDEX idx_customers_email   (email)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- PRODUCTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sku          VARCHAR(80)   NOT NULL UNIQUE,
    name         VARCHAR(255)  NOT NULL,
    category     VARCHAR(100),
    sub_category VARCHAR(100),
    unit_price   DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    cost_price   DECIMAL(10,2) DEFAULT 0.00,
    stock_qty    INT           DEFAULT 0,
    is_active    TINYINT(1)    NOT NULL DEFAULT 1,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_products_category (category),
    INDEX idx_products_sku      (sku)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- TRANSACTIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id      INT UNSIGNED NOT NULL,
    product_id       INT UNSIGNED,
    transaction_date DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount           DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    quantity         INT           NOT NULL DEFAULT 1,
    payment_method   ENUM('credit_card','debit_card','bank_transfer','paypal','crypto','cash') DEFAULT 'credit_card',
    status           ENUM('completed','pending','failed','refunded','disputed') NOT NULL DEFAULT 'completed',
    ip_address       VARCHAR(45),
    device_type      VARCHAR(50),
    country          VARCHAR(100),
    is_flagged       TINYINT(1)    NOT NULL DEFAULT 0,
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)  REFERENCES products(id)  ON DELETE SET NULL,
    INDEX idx_txn_customer    (customer_id),
    INDEX idx_txn_date        (transaction_date),
    INDEX idx_txn_status      (status),
    INDEX idx_txn_flagged     (is_flagged)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- SALES (aggregated daily)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sale_date    DATE         NOT NULL,
    region       VARCHAR(100),
    product_id   INT UNSIGNED,
    revenue      DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    units_sold   INT           NOT NULL DEFAULT 0,
    orders_count INT           NOT NULL DEFAULT 0,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_sales_date   (sale_date),
    INDEX idx_sales_region (region)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- SUPPORT TICKETS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS support_tickets (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id  INT UNSIGNED NOT NULL,
    subject      VARCHAR(255) NOT NULL,
    description  TEXT,
    category     VARCHAR(80),
    priority     ENUM('low','medium','high','critical') DEFAULT 'medium',
    status       ENUM('open','in_progress','resolved','closed') DEFAULT 'open',
    resolved_at  DATETIME,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    INDEX idx_tickets_customer (customer_id),
    INDEX idx_tickets_status   (status),
    INDEX idx_tickets_priority (priority)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- CHURN PREDICTIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS churn_predictions (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id       INT UNSIGNED NOT NULL,
    churn_probability DECIMAL(5,4) NOT NULL CHECK (churn_probability BETWEEN 0 AND 1),
    risk_level        ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL,
    prediction        TINYINT(1)   NOT NULL DEFAULT 0,
    top_features      JSON,
    model_version     VARCHAR(50),
    predicted_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    INDEX idx_churn_customer  (customer_id),
    INDEX idx_churn_risk      (risk_level),
    INDEX idx_churn_predicted (predicted_at)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- FRAUD PREDICTIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fraud_predictions (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_id      INT UNSIGNED NOT NULL,
    fraud_probability   DECIMAL(5,4) NOT NULL CHECK (fraud_probability BETWEEN 0 AND 1),
    risk_level          ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL,
    is_fraud            TINYINT(1)   NOT NULL DEFAULT 0,
    top_features        JSON,
    model_version       VARCHAR(50),
    predicted_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    INDEX idx_fraud_txn       (transaction_id),
    INDEX idx_fraud_risk      (risk_level),
    INDEX idx_fraud_predicted (predicted_at)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- SALES PREDICTIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_predictions (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    forecast_date   DATE         NOT NULL,
    region          VARCHAR(100),
    product_id      INT UNSIGNED,
    predicted_revenue DECIMAL(14,2) NOT NULL,
    lower_bound     DECIMAL(14,2),
    upper_bound     DECIMAL(14,2),
    model_version   VARCHAR(50),
    predicted_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_sp_date   (forecast_date),
    INDEX idx_sp_region (region)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- CUSTOMER SEGMENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customer_segments (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT UNSIGNED NOT NULL UNIQUE,
    segment_label VARCHAR(80)  NOT NULL,
    cluster_id    INT,
    score         DECIMAL(6,4),
    model_version VARCHAR(50),
    segmented_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    INDEX idx_seg_label (segment_label)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- AI QUERIES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_queries (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id      INT UNSIGNED,
    query_text   TEXT         NOT NULL,
    agent_used   VARCHAR(80),
    sources_used JSON,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_ai_queries_user (user_id)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- AI RESPONSES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_responses (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    query_id     INT UNSIGNED NOT NULL,
    response_text TEXT        NOT NULL,
    tokens_used  INT,
    latency_ms   INT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES ai_queries(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- DOCUMENTS (RAG)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    filename     VARCHAR(255) NOT NULL,
    file_path    VARCHAR(512) NOT NULL,
    doc_type     VARCHAR(50),
    category     VARCHAR(100),
    chunk_count  INT DEFAULT 0,
    indexed_at   DATETIME,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_docs_category (category)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- MODEL VERSIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_versions (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    model_name     VARCHAR(100) NOT NULL,
    version        VARCHAR(50)  NOT NULL,
    algorithm      VARCHAR(100),
    accuracy       DECIMAL(6,4),
    f1_score       DECIMAL(6,4),
    roc_auc        DECIMAL(6,4),
    parameters     JSON,
    mlflow_run_id  VARCHAR(100),
    is_active      TINYINT(1) NOT NULL DEFAULT 0,
    trained_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_model_version (model_name, version),
    INDEX idx_mv_model  (model_name),
    INDEX idx_mv_active (is_active)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- AUDIT LOGS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED,
    action      VARCHAR(100) NOT NULL,
    resource    VARCHAR(100),
    resource_id VARCHAR(50),
    ip_address  VARCHAR(45),
    details     JSON,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_user     (user_id),
    INDEX idx_audit_action   (action),
    INDEX idx_audit_created  (created_at)
) ENGINE=InnoDB;
