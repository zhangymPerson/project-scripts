--
-- 回滚文件示例：回滚 001_create_users.sql
-- 命名约定：rollback_NNN.sql
-- 用法：mysql -u user -p database < migrations/rollback_001.sql
--

START TRANSACTION;

-- 删除用户表
DROP TABLE IF EXISTS users;

COMMIT;
