CREATE DATABASE IF NOT EXISTS suitecrm_clientea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS suitecrm_clienteb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'suitecrm_user'@'%' IDENTIFIED BY 'suitecrm_pass';

GRANT ALL PRIVILEGES ON *.* TO 'suitecrm_user'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;