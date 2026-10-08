import pymysql

# 让 Django 的 MySQL 后端使用 PyMySQL 驱动(与原 FastAPI 后端一致)
pymysql.install_as_MySQLdb()
