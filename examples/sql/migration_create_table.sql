--
-- 迁移文件示例：创建用户表
-- 命名约定：NNN_描述.sql
-- 用法：mysql -u user -p database < migrations/001_create_users.sql
--

-- 开始事务（确保原子性）
START TRANSACTION;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '用户 ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',

    -- 状态字段
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0=禁用，1=正常，2=锁定',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已验证',

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL DEFAULT NULL COMMENT '删除时间（软删除）',

    -- 索引
    INDEX idx_users_email (email),
    INDEX idx_users_status (status),
    INDEX idx_users_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 提交事务
COMMIT;
