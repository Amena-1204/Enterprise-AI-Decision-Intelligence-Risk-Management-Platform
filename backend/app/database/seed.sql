-- Enterprise AI Platform — Seed Data
-- Realistic demo data for development and testing
USE enterprise_ai;

-- ─────────────────────────────────────────────
-- USERS  (passwords are hashed via app; these are placeholder hashes)
-- ─────────────────────────────────────────────
INSERT INTO users (username, email, password_hash, role) VALUES
('admin',        'admin@enterprise.ai',   'PLACEHOLDER_HASH', 'admin'),
('alice_analyst','alice@enterprise.ai',   'PLACEHOLDER_HASH', 'analyst'),
('bob_viewer',   'bob@enterprise.ai',     'PLACEHOLDER_HASH', 'viewer');

-- ─────────────────────────────────────────────
-- PRODUCTS
-- ─────────────────────────────────────────────
INSERT INTO products (sku, name, category, sub_category, unit_price, cost_price, stock_qty) VALUES
('PRD-001', 'Enterprise CRM Suite',       'Software',  'CRM',        1200.00, 200.00, 999),
('PRD-002', 'Analytics Dashboard Pro',    'Software',  'Analytics',   800.00, 120.00, 999),
('PRD-003', 'AI Insights Module',         'Software',  'AI',         2500.00, 400.00, 999),
('PRD-004', 'Data Warehouse Connector',   'Software',  'Integration', 600.00,  80.00, 999),
('PRD-005', 'Security Compliance Pack',   'Software',  'Security',    950.00, 150.00, 999),
('PRD-006', 'Mobile Field App',           'Software',  'Mobile',      400.00,  60.00, 999),
('PRD-007', 'Premium Support Plan',       'Service',   'Support',     300.00,  50.00, 999),
('PRD-008', 'Onboarding Consulting',      'Service',   'Consulting', 1500.00, 300.00, 999),
('PRD-009', 'Custom Integration Service', 'Service',   'Consulting', 3000.00, 600.00, 999),
('PRD-010', 'Training & Certification',   'Training',  'Education',   500.00,  80.00, 999);

-- ─────────────────────────────────────────────
-- CUSTOMERS  (30 realistic customers)
-- ─────────────────────────────────────────────
INSERT INTO customers (external_id, first_name, last_name, email, phone, region, country, segment, acquisition_channel, lifetime_value, total_orders, last_purchase_date, account_age_days) VALUES
('C001','James',    'Harrison', 'james.harrison@techcorp.com',   '+1-555-0101','North America','US','High Value',    'Direct',       45200.00, 38, '2024-11-15', 1200),
('C002','Sarah',    'Mitchell', 'sarah.mitchell@globalinc.com',  '+1-555-0102','North America','US','Loyal',         'Referral',     28900.00, 24, '2024-12-01', 980),
('C003','David',    'Chen',     'david.chen@asiapac.com',        '+86-555-0103','Asia Pacific', 'CN','High Value',   'Partner',      62100.00, 51, '2024-12-10', 1450),
('C004','Emma',     'Williams', 'emma.williams@eurocorp.eu',     '+44-555-0104','Europe',       'GB','Loyal',        'Organic',      19400.00, 17, '2024-10-20', 720),
('C005','Carlos',   'Rodriguez','carlos.rodriguez@latam.com',    '+52-555-0105','Latin America','MX','At Risk',      'Paid Search',   8200.00,  9, '2024-08-05', 540),
('C006','Priya',    'Sharma',   'priya.sharma@indiabiz.in',      '+91-555-0106','Asia Pacific', 'IN','New Customer',  'Social Media',  1200.00,  2, '2024-12-05', 45),
('C007','Michael',  'Johnson',  'michael.johnson@midwest.com',   '+1-555-0107', 'North America','US','High Value',   'Direct',       38700.00, 32, '2024-11-28', 1100),
('C008','Yuki',     'Tanaka',   'yuki.tanaka@jptech.jp',         '+81-555-0108','Asia Pacific', 'JP','Loyal',        'Partner',      22300.00, 19, '2024-11-10', 860),
('C009','Anna',     'Kowalski', 'anna.kowalski@polbiz.pl',       '+48-555-0109','Europe',       'PL','At Risk',      'Organic',       5600.00,  6, '2024-07-15', 430),
('C010','Robert',   'Thompson', 'robert.thompson@usatech.com',   '+1-555-0110', 'North America','US','Low Engagement','Email',        3100.00,  4, '2024-06-20', 380),
('C011','Fatima',   'Al-Hassan','fatima.alhassan@mena.ae',       '+971-555-0111','Middle East',  'AE','New Customer', 'Paid Search',   2800.00,  3, '2024-12-08', 60),
('C012','Thomas',   'Mueller',  'thomas.mueller@germtech.de',    '+49-555-0112','Europe',       'DE','High Value',   'Direct',       41500.00, 35, '2024-12-02', 1050),
('C013','Lisa',     'Anderson', 'lisa.anderson@startup.io',      '+1-555-0113', 'North America','US','At Risk',      'Referral',      7400.00,  8, '2024-09-10', 490),
('C014','Wei',      'Zhang',    'wei.zhang@chinatech.cn',        '+86-555-0114','Asia Pacific', 'CN','Loyal',        'Partner',      31200.00, 26, '2024-11-20', 920),
('C015','Sophie',   'Dubois',   'sophie.dubois@frenchco.fr',     '+33-555-0115','Europe',       'FR','High Value',   'Direct',       55800.00, 46, '2024-12-07', 1300),
('C016','Ahmed',    'Ibrahim',  'ahmed.ibrahim@africabiz.ng',    '+234-555-0116','Africa',       'NG','New Customer', 'Social Media',   900.00,  1, '2024-12-09', 30),
('C017','Jennifer', 'Davis',    'jennifer.davis@consulting.com', '+1-555-0117', 'North America','US','Loyal',        'Direct',       24600.00, 21, '2024-11-05', 800),
('C018','Hiroshi',  'Yamamoto', 'hiroshi.yamamoto@jpbiz.jp',     '+81-555-0118','Asia Pacific', 'JP','At Risk',      'Organic',       6800.00,  7, '2024-08-25', 460),
('C019','Maria',    'Garcia',   'maria.garcia@spainco.es',       '+34-555-0119','Europe',       'ES','Low Engagement','Email',        4200.00,  5, '2024-07-30', 410),
('C020','Kevin',    'Brown',    'kevin.brown@techstart.com',     '+1-555-0120', 'North America','US','High Value',   'Referral',     47300.00, 40, '2024-12-03', 1180),
('C021','Nadia',    'Petrov',   'nadia.petrov@rusbiz.ru',        '+7-555-0121', 'Europe',       'RU','At Risk',      'Paid Search',   5100.00,  6, '2024-08-15', 420),
('C022','Daniel',   'Wilson',   'daniel.wilson@ausbiz.au',       '+61-555-0122','Asia Pacific', 'AU','Loyal',        'Direct',       18700.00, 16, '2024-10-30', 700),
('C023','Amara',    'Diallo',   'amara.diallo@westafr.sn',       '+221-555-0123','Africa',      'SN','New Customer', 'Social Media',  1500.00,  2, '2024-12-06', 55),
('C024','Chris',    'Taylor',   'chris.taylor@canadaco.ca',      '+1-555-0124', 'North America','CA','High Value',   'Direct',       36900.00, 31, '2024-11-25', 1080),
('C025','Elena',    'Rossi',    'elena.rossi@italyco.it',        '+39-555-0125','Europe',       'IT','Loyal',        'Organic',      21800.00, 18, '2024-11-15', 840),
('C026','Omar',     'Khalid',   'omar.khalid@gulfbiz.sa',        '+966-555-0126','Middle East',  'SA','Low Engagement','Email',       3800.00,  4, '2024-07-05', 390),
('C027','Rachel',   'Green',    'rachel.green@nycorp.com',       '+1-555-0127', 'North America','US','At Risk',      'Referral',      9100.00, 10, '2024-09-20', 510),
('C028','Kenji',    'Nakamura', 'kenji.nakamura@tokyotech.jp',   '+81-555-0128','Asia Pacific', 'JP','High Value',   'Partner',      58400.00, 48, '2024-12-11', 1380),
('C029','Isabelle', 'Laurent',  'isabelle.laurent@belgianco.be', '+32-555-0129','Europe',       'BE','Loyal',        'Direct',       26100.00, 22, '2024-11-08', 870),
('C030','Marcus',   'Johnson',  'marcus.johnson@southco.com',    '+1-555-0130', 'North America','US','Low Engagement','Paid Search',  2500.00,  3, '2024-06-10', 360);

-- ─────────────────────────────────────────────
-- TRANSACTIONS  (sample transactions)
-- ─────────────────────────────────────────────
INSERT INTO transactions (customer_id, product_id, transaction_date, amount, quantity, payment_method, status, ip_address, device_type, country) VALUES
(1,  1, '2024-11-15 10:23:00', 1200.00, 1, 'credit_card',    'completed', '192.168.1.10', 'desktop', 'US'),
(1,  3, '2024-10-05 14:11:00', 2500.00, 1, 'bank_transfer',  'completed', '192.168.1.10', 'desktop', 'US'),
(2,  2, '2024-12-01 09:45:00',  800.00, 1, 'credit_card',    'completed', '10.0.0.22',    'laptop',  'US'),
(3,  3, '2024-12-10 16:30:00', 5000.00, 2, 'bank_transfer',  'completed', '203.0.113.5',  'desktop', 'CN'),
(3,  1, '2024-11-01 11:00:00', 1200.00, 1, 'bank_transfer',  'completed', '203.0.113.5',  'desktop', 'CN'),
(4,  2, '2024-10-20 13:20:00',  800.00, 1, 'credit_card',    'completed', '198.51.100.1', 'laptop',  'GB'),
(5,  6, '2024-08-05 08:15:00',  400.00, 1, 'paypal',         'completed', '172.16.0.5',   'mobile',  'MX'),
(6,  6, '2024-12-05 17:00:00',  400.00, 1, 'credit_card',    'completed', '10.10.10.10',  'mobile',  'IN'),
(7,  1, '2024-11-28 12:00:00', 1200.00, 1, 'credit_card',    'completed', '192.0.2.1',    'desktop', 'US'),
(7,  3, '2024-09-15 10:30:00', 2500.00, 1, 'bank_transfer',  'completed', '192.0.2.1',    'desktop', 'US'),
(8,  2, '2024-11-10 15:45:00',  800.00, 1, 'credit_card',    'completed', '198.18.0.1',   'laptop',  'JP'),
(9,  7, '2024-07-15 09:00:00',  300.00, 1, 'paypal',         'completed', '203.0.113.20', 'desktop', 'PL'),
(10, 6, '2024-06-20 11:30:00',  400.00, 1, 'debit_card',     'completed', '192.168.2.5',  'mobile',  'US'),
(12, 1, '2024-12-02 14:00:00', 1200.00, 1, 'bank_transfer',  'completed', '198.51.100.5', 'desktop', 'DE'),
(12, 3, '2024-10-10 10:00:00', 2500.00, 1, 'bank_transfer',  'completed', '198.51.100.5', 'desktop', 'DE'),
(13, 7, '2024-09-10 16:00:00',  300.00, 1, 'credit_card',    'completed', '10.20.30.40',  'laptop',  'US'),
(14, 2, '2024-11-20 13:00:00',  800.00, 1, 'credit_card',    'completed', '203.0.113.30', 'desktop', 'CN'),
(15, 3, '2024-12-07 11:30:00', 2500.00, 1, 'bank_transfer',  'completed', '198.51.100.10','desktop', 'FR'),
(15, 9, '2024-11-01 09:00:00', 3000.00, 1, 'bank_transfer',  'completed', '198.51.100.10','desktop', 'FR'),
(17, 1, '2024-11-05 10:00:00', 1200.00, 1, 'credit_card',    'completed', '192.168.3.1',  'desktop', 'US'),
(20, 3, '2024-12-03 15:00:00', 2500.00, 1, 'bank_transfer',  'completed', '10.0.1.1',     'desktop', 'US'),
(20, 1, '2024-10-20 12:00:00', 1200.00, 1, 'credit_card',    'completed', '10.0.1.1',     'desktop', 'US'),
(24, 1, '2024-11-25 14:30:00', 1200.00, 1, 'bank_transfer',  'completed', '192.168.4.1',  'desktop', 'CA'),
(24, 5, '2024-10-15 11:00:00',  950.00, 1, 'bank_transfer',  'completed', '192.168.4.1',  'desktop', 'CA'),
(28, 3, '2024-12-11 16:00:00', 2500.00, 1, 'bank_transfer',  'completed', '203.0.113.50', 'desktop', 'JP'),
(28, 9, '2024-11-15 10:00:00', 3000.00, 1, 'bank_transfer',  'completed', '203.0.113.50', 'desktop', 'JP'),
-- Suspicious / fraud-flagged transactions
(5,  3, '2024-11-20 02:33:00', 7500.00, 3, 'credit_card',    'completed', '45.33.32.156', 'unknown', 'RU'),
(10, 3, '2024-11-25 03:15:00', 5000.00, 2, 'crypto',         'completed', '185.220.101.1','unknown', 'CN'),
(19, 1, '2024-11-28 01:45:00', 4800.00, 4, 'credit_card',    'disputed',  '91.108.4.1',   'unknown', 'UA'),
(21, 3, '2024-12-01 04:00:00', 6200.00, 2, 'crypto',         'failed',    '185.220.101.5','unknown', 'RU');

-- Mark flagged transactions
UPDATE transactions SET is_flagged = 1 WHERE id IN (27, 28, 29, 30);

-- ─────────────────────────────────────────────
-- SALES  (daily aggregated — last 90 days)
-- ─────────────────────────────────────────────
INSERT INTO sales (sale_date, region, product_id, revenue, units_sold, orders_count) VALUES
('2024-09-15','North America', 1, 12000.00, 10, 10),
('2024-09-15','Europe',        2,  6400.00,  8,  8),
('2024-09-15','Asia Pacific',  3, 17500.00,  7,  7),
('2024-09-22','North America', 1, 14400.00, 12, 12),
('2024-09-22','Europe',        2,  8000.00, 10, 10),
('2024-09-29','North America', 3, 22500.00,  9,  9),
('2024-09-29','Asia Pacific',  1,  9600.00,  8,  8),
('2024-10-06','North America', 1, 16800.00, 14, 14),
('2024-10-06','Europe',        5,  9500.00, 10, 10),
('2024-10-06','Latin America', 6,  3200.00,  8,  8),
('2024-10-13','North America', 3, 25000.00, 10, 10),
('2024-10-13','Asia Pacific',  2,  8000.00, 10, 10),
('2024-10-20','Europe',        1, 13200.00, 11, 11),
('2024-10-20','North America', 2, 11200.00, 14, 14),
('2024-10-27','North America', 1, 18000.00, 15, 15),
('2024-10-27','Asia Pacific',  3, 30000.00, 12, 12),
('2024-11-03','North America', 3, 27500.00, 11, 11),
('2024-11-03','Europe',        2,  9600.00, 12, 12),
('2024-11-10','North America', 1, 20400.00, 17, 17),
('2024-11-10','Asia Pacific',  1, 12000.00, 10, 10),
('2024-11-17','North America', 5, 14250.00, 15, 15),
('2024-11-17','Europe',        3, 22500.00,  9,  9),
('2024-11-24','North America', 1, 22800.00, 19, 19),
('2024-11-24','Asia Pacific',  2, 12800.00, 16, 16),
('2024-12-01','North America', 3, 32500.00, 13, 13),
('2024-12-01','Europe',        1, 15600.00, 13, 13),
('2024-12-08','North America', 1, 24000.00, 20, 20),
('2024-12-08','Asia Pacific',  3, 35000.00, 14, 14),
('2024-12-08','Latin America', 6,  4800.00, 12, 12);

-- ─────────────────────────────────────────────
-- SUPPORT TICKETS
-- ─────────────────────────────────────────────
INSERT INTO support_tickets (customer_id, subject, description, category, priority, status, resolved_at) VALUES
(5,  'Cannot access dashboard',       'Login fails after password reset',          'Technical',  'high',     'resolved', '2024-08-10 14:00:00'),
(9,  'Billing discrepancy',           'Charged twice for the same subscription',   'Billing',    'high',     'resolved', '2024-07-20 10:00:00'),
(10, 'Feature request: export CSV',   'Need CSV export for reports',               'Feature',    'low',      'closed',   '2024-07-01 09:00:00'),
(13, 'Integration not working',       'Salesforce connector returns 401 errors',   'Technical',  'critical', 'resolved', '2024-09-15 16:00:00'),
(18, 'Slow performance',              'Dashboard takes 30+ seconds to load',       'Performance','medium',   'in_progress', NULL),
(19, 'Wrong invoice amount',          'Invoice shows incorrect tax calculation',   'Billing',    'medium',   'open',     NULL),
(21, 'Account locked',                'Account locked after 3 failed attempts',    'Security',   'high',     'resolved', '2024-08-20 11:00:00'),
(27, 'Data not syncing',              'Customer data not syncing from CRM',        'Technical',  'high',     'open',     NULL),
(5,  'Refund request',                'Requesting refund for unused licenses',     'Billing',    'medium',   'in_progress', NULL),
(13, 'API rate limit exceeded',       'Getting 429 errors on bulk operations',     'Technical',  'medium',   'open',     NULL);

-- ─────────────────────────────────────────────
-- CHURN PREDICTIONS  (sample)
-- ─────────────────────────────────────────────
INSERT INTO churn_predictions (customer_id, churn_probability, risk_level, prediction, top_features, model_version) VALUES
(5,  0.8200, 'HIGH',     1, '["low_purchase_frequency","multiple_support_tickets","long_inactivity"]', 'v1.0'),
(9,  0.7500, 'HIGH',     1, '["billing_dispute","inactivity_90_days","low_lifetime_value"]',           'v1.0'),
(10, 0.6800, 'HIGH',     1, '["low_engagement","no_recent_purchase","low_order_count"]',               'v1.0'),
(13, 0.7100, 'HIGH',     1, '["technical_issues","integration_failure","at_risk_segment"]',            'v1.0'),
(18, 0.5900, 'MEDIUM',   1, '["performance_complaints","declining_usage","asia_pacific_region"]',      'v1.0'),
(19, 0.5400, 'MEDIUM',   0, '["billing_issue","low_engagement","europe_region"]',                      'v1.0'),
(21, 0.6200, 'HIGH',     1, '["security_incident","account_locked","low_ltv"]',                        'v1.0'),
(27, 0.4800, 'MEDIUM',   0, '["data_sync_issue","at_risk_segment","referral_channel"]',                'v1.0'),
(1,  0.0800, 'LOW',      0, '["high_ltv","frequent_purchases","long_tenure"]',                         'v1.0'),
(3,  0.0500, 'LOW',      0, '["highest_ltv","partner_channel","asia_high_value"]',                     'v1.0'),
(15, 0.0600, 'LOW',      0, '["high_ltv","recent_purchase","europe_high_value"]',                      'v1.0'),
(28, 0.0400, 'LOW',      0, '["highest_orders","partner_channel","japan_high_value"]',                 'v1.0');

-- ─────────────────────────────────────────────
-- FRAUD PREDICTIONS  (for flagged transactions)
-- ─────────────────────────────────────────────
INSERT INTO fraud_predictions (transaction_id, fraud_probability, risk_level, is_fraud, top_features, model_version) VALUES
(27, 0.9200, 'CRITICAL', 1, '["unusual_hour","foreign_ip","high_amount","crypto_payment"]',  'v1.0'),
(28, 0.8700, 'CRITICAL', 1, '["unusual_hour","tor_exit_node","high_amount","unknown_device"]','v1.0'),
(29, 0.7800, 'HIGH',     1, '["unusual_hour","disputed_status","high_quantity","ukraine_ip"]','v1.0'),
(30, 0.8100, 'HIGH',     1, '["unusual_hour","failed_status","crypto_payment","russia_ip"]', 'v1.0');

-- ─────────────────────────────────────────────
-- CUSTOMER SEGMENTS
-- ─────────────────────────────────────────────
INSERT INTO customer_segments (customer_id, segment_label, cluster_id, score, model_version) VALUES
(1,  'High Value',      0, 0.9200, 'v1.0'),
(2,  'Loyal',           1, 0.8100, 'v1.0'),
(3,  'High Value',      0, 0.9600, 'v1.0'),
(4,  'Loyal',           1, 0.7800, 'v1.0'),
(5,  'At Risk',         2, 0.7200, 'v1.0'),
(6,  'New Customer',    3, 0.6500, 'v1.0'),
(7,  'High Value',      0, 0.9100, 'v1.0'),
(8,  'Loyal',           1, 0.8000, 'v1.0'),
(9,  'At Risk',         2, 0.6900, 'v1.0'),
(10, 'Low Engagement',  4, 0.5800, 'v1.0'),
(11, 'New Customer',    3, 0.6200, 'v1.0'),
(12, 'High Value',      0, 0.9300, 'v1.0'),
(13, 'At Risk',         2, 0.6800, 'v1.0'),
(14, 'Loyal',           1, 0.8200, 'v1.0'),
(15, 'High Value',      0, 0.9500, 'v1.0'),
(16, 'New Customer',    3, 0.6000, 'v1.0'),
(17, 'Loyal',           1, 0.7900, 'v1.0'),
(18, 'At Risk',         2, 0.6600, 'v1.0'),
(19, 'Low Engagement',  4, 0.5500, 'v1.0'),
(20, 'High Value',      0, 0.9400, 'v1.0'),
(21, 'At Risk',         2, 0.7000, 'v1.0'),
(22, 'Loyal',           1, 0.7700, 'v1.0'),
(23, 'New Customer',    3, 0.6300, 'v1.0'),
(24, 'High Value',      0, 0.9000, 'v1.0'),
(25, 'Loyal',           1, 0.8100, 'v1.0'),
(26, 'Low Engagement',  4, 0.5600, 'v1.0'),
(27, 'At Risk',         2, 0.6700, 'v1.0'),
(28, 'High Value',      0, 0.9700, 'v1.0'),
(29, 'Loyal',           1, 0.8000, 'v1.0'),
(30, 'Low Engagement',  4, 0.5400, 'v1.0');

-- ─────────────────────────────────────────────
-- MODEL VERSIONS
-- ─────────────────────────────────────────────
INSERT INTO model_versions (model_name, version, algorithm, accuracy, f1_score, roc_auc, is_active) VALUES
('churn_model',        'v1.0', 'RandomForestClassifier', 0.8720, 0.8340, 0.9120, 1),
('fraud_model',        'v1.0', 'XGBClassifier',          0.9450, 0.9210, 0.9780, 1),
('sales_forecast',     'v1.0', 'LinearRegression',       NULL,   NULL,   NULL,   1),
('segmentation_model', 'v1.0', 'KMeans',                 NULL,   NULL,   NULL,   1);
