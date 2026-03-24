--
-- 迁移文件示例：添加字段
-- 命名约定：NNN_描述.sql
-- 用法：mysql -u user -p database < migrations/002_add_phone_to_users.sql
--

START TRANSACTION;

-- 添加手机号字段
ALTER TABLE users
ADD COLUMN phone VARCHAR(20) NULL UNIQUE COMMENT '手机号'
AFTER email;

-- 添加手机号索引
ALTER TABLE users
ADD INDEX idx_users_phone (phone);

-- 添加验证时间字段
ALTER TABLE users
ADD COLUMN verified_at TIMESTAMP NULL DEFAULT NULL COMMENT '验证时间'
AFTER is_verified;

COMMIT;
