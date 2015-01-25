__author__ = 'adrien'

import sqlite3


class MetaHandler:
    def __init__(self):
        self.db_path = "/home/adrien/Documents/PycharmProjects/tests/bla.db"
        self.db_path_ro = "file:" + self.db_path + "?mode=ro"
        self.hourra = "Hourra !"
        print(self.hourra)

    def New(self, database, data, vuid=None):
        """this method is used to create new entries in the database"""
        self.database = database
        self.data = data
        self.vuid = vuid

        self.con = sqlite3.connect(self.db_path)
        self.con.isolation_level = 'EXCLUSIVE'
        self.cur = self.con.cursor()
        self.con.execute('BEGIN EXCLUSIVE')
        # self.cur.execute("CREATE TABLE DublinCore(vuid int, subject text, object text)")
        # self.cur.execute("CREATE TABLE FilePathByFormat(vuid int, codec text, path text)")
        # self.cur.execute("delete from DublinCore")

        if self.database == "DublinCore":
            # Check if a vuid is provided, if not calculate one
            if self.vuid == None:
                self.cur.execute("select max(vuid) from DublinCore")
                try:
                    self.vuid = self.cur.fetchone()[0] + 1
                except TypeError:
                    self.vuid = 0
            # Fill the database
            for self.key, self.v in self.data.items():
                for self.value in self.v:
                    self.sql = (self.vuid, self.key, self.value)
                    # check if the value doesn't already exist
                    self.cur.execute('''select * from DublinCore where vuid=? and subject=? and object=?''', self.sql)
                    if not self.cur.fetchone():
                        self.cur.execute("INSERT INTO DublinCore VALUES (?,?,?)", self.sql)
                    else:
                        self.con.close()
                        raise ValueError(self.sql)

        elif self.database == "FilePathByFormat":
            # Check if a vuid is provided, if not raise an error
            if not self.vuid:
                raise ValueError("vuid not provided")
            for self.key, self.v in self.data.items():
                for self.value in self.v:
                    self.sql = (self.vuid, self.key, self.value)
                    # check if the value doesn't already exist
                    self.cur.execute('''select * from FilePathByFormat where vuid=? and codec=? and path=?''', self.sql)
                    if not self.cur.fetchone():
                        # fill the database
                        self.cur.execute("INSERT INTO FilePathByFormat VALUES (?,?,?)", self.sql)
                    else:
                        self.con.close()
                        raise ValueError(self.sql)
        else:
            raise ValueError("unexpected input")

        self.con.commit()
        self.con.close()
        return (self.vuid)

    def Search(self, database, data=None, vuid=None):
        self.database = database
        self.data = data
        self.vuid = vuid

        self.con = sqlite3.connect(self.db_path_ro, uri=True)
        #self.con.isolation_level = 'EXCLUSIVE'
        self.cur = self.con.cursor()
        #self.con.execute('BEGIN EXCLUSIVE')

        if self.database == "DublinCore":

            if self.vuid and self.data:
                self.data_fetchall = []
                for self.key, self.v in self.data.items():
                    for self.value in self.v:
                        self.sql = (self.vuid, self.key, self.value)
                        # check if the value doesn't already exist
                        self.cur.execute('''select * from DublinCore where vuid=? and subject=? and object=?''', self.sql)
                        self.data_fetchall.append(self.cur.fetchall())
            elif self.vuid:
                self.tuple = (self.vuid,)
                self.cur.execute('''select * from DublinCore where vuid=?''', self.tuple)
                self.data_fetchall = self.cur.fetchall()

            elif self.data:
                self.data_fetchall = []
                for self.key, self.v in self.data.items():
                    for self.value in self.v:
                        self.sql = (self.key, self.value)
                        # check if the value doesn't already exist
                        self.cur.execute('''select * from DublinCore where subject=? and object=?''', self.sql)
                        self.data_fetchall.append(self.cur.fetchall())
            else:
                self.cur.execute('''select * from DublinCore''')
                self.data_fetchall = self.cur.fetchall()


        elif self.database == "FilePathByFormat":

            if self.vuid and self.data:
                self.data_fetchall = []
                for self.key, self.v in self.data.items():
                    for self.value in self.v:
                        self.sql = (self.vuid, self.value)

                        self.cur.execute('''select * from FilePathByFormat where vuid=? and codec=?''', self.sql)
                        self.data_fetchall.append(self.cur.fetchall())
            elif self.vuid:
                self.tuple = (self.vuid,)
                self.cur.execute('''select * from FilePathByFormat where vuid=?''', self.tuple)
                self.data_fetchall = self.cur.fetchall()

            elif self.data:
                self.data_fetchall = []
                for self.key, self.v in self.data.items():
                    for self.value in self.v:
                        self.sql = (self.value,)
                        # check if the value doesn't already exist
                        self.cur.execute('''select * from FilePathByFormat where codec=?''', self.sql)
                        self.data_fetchall.append(self.cur.fetchall())
            else:
                self.cur.execute('''select * from FilePathByFormat''')
                self.data_fetchall = self.cur.fetchall()

            print(self.data_fetchall)
        self.con.close()



the_object = MetaHandler()
if 1:
    dict = {"codec": ("ffv1",)}
    the_object.Search("FilePathByFormat", data=dict, vuid=10)
else:
    dict = {"actor": ("george", "machin")}
    the_object.New("DublinCore", dict)