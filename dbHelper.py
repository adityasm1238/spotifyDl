import sqlite3
from sqlite3 import Error

class DBHelper:
    def __init__(self,db='spotipyDb'):
        self.con = None
        try:
            self.con = sqlite3.connect(db)
        except Error as e:
            print(e)
        if(self.con!=None):
            cur = self.con.cursor()
            sql = "CREATE TABLE IF NOT EXISTS data (id TEXT ,songId TEXT)"
            cur.execute(sql)
            self.con.commit()
    
    def isNew(self,uid,songId):
        cur = self.con.cursor()
        cur.execute("select * from data where id = ? AND songId = ?",(uid,songId))
        return len(cur.fetchall())==0
    
    def insertData(self,uid,songId):
        cur = self.con.cursor()
        cur.execute("insert into data values (?,?)",(uid,songId))
        self.con.commit()

    def close(self):
        self.con.close()