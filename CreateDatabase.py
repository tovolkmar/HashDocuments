import sqlite3
con = sqlite3.connect("documents.db")
cur = con.cursor()
cur.execute("CREATE TABLE documents(filepath, hash)")