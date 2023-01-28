import json
import random
import sqlite3
import datetime

conn = sqlite3.connect("./Resources/db/cov.db")
cov_db = conn.cursor()


class CovInfo:

    def __init__(self, *user_id:int) -> None:
        self.qq:int = user_id[0] if user_id else 0
        self.at_time:int
        self.hour:int = datetime.datetime.now().hour
        self.proto_hour:int = (datetime.datetime.now()+datetime.timedelta(hours=-1)).hour

    def createTable(self) -> None:
        cov_db.execute(f"""CREATE TABLE "{self.hour}" (
                "qq" integer NOT NULL,
                "at_time" integer,
                "poke_time" integer,
                PRIMARY KEY ("qq"));""")

    def dropTable(self) -> None:
        cov_db.execute(f"""DROP TABLE '{self.proto_hour}'""")


class AtInfo(CovInfo):

    def __init__(self, *user_id: int) -> None:
        super().__init__(*user_id)
        try:
            _ = cov_db.execute(f"""SELECT at_time FROM "{self.hour}" WHERE qq={self.qq}""").fetchall()[0][0]
            self.at_time:int = _ if _ else 0
        except:
            self.at_time:int = 1


    def addAt(self) -> None:
        try:
            if cov_db.execute(f"""SELECT * FROM "{self.hour}" WHERE qq={self.qq}""").fetchall():
                cov_db.execute(f"""UPDATE "main"."{self.hour}" SET "at_time" = {self.at_time+1} WHERE rowid = {self.qq}""")
            else:
                cov_db.execute(f"""INSERT INTO "main"."{self.hour}" ("qq", "at_time") VALUES ({self.qq}, {self.at_time+1})""")
        except:
            self.createTable()
            self.addAt()
        conn.commit()

    def getAtMsg(self) -> str:
        with open("./Resources/Json/wordbank.json","r",encoding="utf-8") as f:
            at_msg_reply  = json.load(f)['public']['preinstall_words']['at_msg_reply']
        v1 = random.randint(5,7)
        v2 = random.randint(10,12)
        if self.at_time <= v1:
            at_arg = "normal"
        elif v1<= self.at_time <= v2:
            at_arg = "annoy"
        else:
            at_arg = "rage"
        return random.choice(at_msg_reply[at_arg])


class PokeInfo(CovInfo):

    def __init__(self, *user_id: int) -> None:
        super().__init__(*user_id)
        self.poke_time:int = 0
        try:
            _ = cov_db.execute(f"""SELECT poke_time FROM "{self.hour}" WHERE qq={self.qq}""").fetchall()[0][0]
            self.poke_time:int = _ if _ else 0
        except:
            self.poke_time :int= 1

    def addPoke(self) -> None:
        try:
            if cov_db.execute(f"""SELECT * FROM "{self.hour}" WHERE qq={self.qq}""").fetchall():
                cov_db.execute(f"""UPDATE "main"."{self.hour}" SET "poke_time" = {self.poke_time+1} WHERE rowid = {self.qq}""")
            else:
                cov_db.execute(f"""INSERT INTO "main"."{self.hour}" ("qq", "poke_time") VALUES ({self.qq}, {self.poke_time+1})""")
        except:
            self.createTable()
            self.addPoke()
        conn.commit()

    def getPokeMsg(self) -> str:
        with open("./Resources/Json/wordbank.json","r",encoding="utf-8") as f:
            poke_msg_reply  = json.load(f)['public']['preinstall_words']['poke_msg_reply']
        v1 = random.randint(5,7)
        v2 = random.randint(10,12)
        if self.poke_time <= v1:
            poke_arg = "normal"
        elif v1<= self.at_time <= v2:
            poke_arg = "annoy"
        else:
            poke_arg = "rage"
        return random.choice(poke_msg_reply[poke_arg])