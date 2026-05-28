CREATE DATABASE IF NOT EXISTS suitecrm_clientea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS suitecrm_clienteb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'suitecrm_user'@'%' IDENTIFIED BY 'suitecrm_password';

GRANT ALL PRIVILEGES ON suitecrm_clientea.* TO 'suitecrm_user'@'%';
GRANT ALL PRIVILEGES ON suitecrm_clienteb.* TO 'suitecrm_user'@'%';

FLUSH PRIVILEGES;
