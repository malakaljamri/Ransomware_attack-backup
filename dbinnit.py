import sqlite3

conn = sqlite3.connect('DataBase.db')
print ("Opened database successfully")

conn.execute("DROP TABLE IF EXISTS users;")

conn.execute('CREATE TABLE users (name TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, xp INT DEFAULT 0, malwareinfo INT DEFAULT 0 NOT NULL, sqlinjection1 INT  DEFAULT 0 NOT NULL ,  sqlinjection2 INT  DEFAULT 0 NOT NULL , shutdown INT  DEFAULT 0 NOT NULL , final INT  DEFAULT 0 NOT NULL)')
print ("Table created successfully")
conn.close()

