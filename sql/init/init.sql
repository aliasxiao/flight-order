-- 创建用户
create user "flight"@"%" identified by "test";
-- 授予权限
grant all privileges on flight.* to 'flight'@'%';
-- 刷新
flush privileges;