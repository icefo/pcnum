__author__ = 'adrien'

import sqlite3
import itertools


class MetaHandler:
    def __init__(self):
        self.db_path = "/home/adrien/Documents/PycharmProjects/Pc_num/other/old/bla.db"
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
            if not self.vuid:
                self.cur.execute("select max(vuid) from DublinCore")
                try:
                    self.vuid = self.cur.fetchone()[0] + 1
                except TypeError:
                    self.vuid = 0
            else:
                self.cur.execute("select max(vuid) from DublinCore")
                if self.vuid > (self.cur.fetchone()[0] + 1):
                    raise ValueError
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
        """
        :param database: put here the table you want to query
        :param data: give a dict with key = object and value(s) = subject
        :param vuid: give the video unique identifier of the video
        :return: list of tuples [(vuid, object, subject), (16, actor, mario)]]
        """
        self.database = database
        self.data = data
        self.vuid = vuid

        self.con = sqlite3.connect(self.db_path_ro, uri=True)
        #self.con.isolation_level = 'EXCLUSIVE'
        self.cur = self.con.cursor()
        #self.con.execute('BEGIN EXCLUSIVE')

        if self.database == "DublinCore":

            if self.vuid and self.data:

                for self.key, self.v in self.data.items():
                    if self.v:
                        for self.value in self.v:
                            self.sql = (self.vuid, self.key, self.value)

                            self.cur.execute('''select * from DublinCore where vuid=? and subject=? and object=?''', self.sql)
                            self.data_fetchall.append(self.cur.fetchall())
                    else:
                        self.sql = (self.vuid, self.key)

                        self.cur.execute('''select * from DublinCore where vuid=? and subject=?''', self.sql)
                        self.data_fetchall.append(self.cur.fetchall())

            elif self.vuid:
                self.data_fetchall = {}
                # print(self.vuid)
                for self.number in self.vuid:
                    self.tuple = (self.number,)
                    self.cur.execute('''select * from DublinCore where vuid=?''', self.tuple)
                    for self.tuplevalue in self.cur.fetchall():
                        #print(self.tuplevalue)
                        try:
                            self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]].append(self.tuplevalue[2])
                        except KeyError:
                            try:
                                self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]] = [self.tuplevalue[2]]
                            except KeyError:
                                self.data_fetchall[self.tuplevalue[0]] = {}
                                self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]] = [self.tuplevalue[2]]
                print(self.data_fetchall)

            elif self.data:
                for self.key, self.v in self.data.items():
                    if self.v:
                        for self.value in self.v:
                            self.sql = (self.key, self.value)

                            self.cur.execute('''select vuid from DublinCore where subject=? and object=?''', self.sql)
                            self.sqlfetch = self.cur.fetchall()
                            # print(self.sqlfetch)
                            if self.sqlfetch:
                                self.Search("DublinCore", vuid=set(itertools.chain.from_iterable(self.sqlfetch)))
                    else:
                        self.sql = (self.key,)

                        self.cur.execute('''select vuid from DublinCore where subject=?''', self.sql)
                        self.sqlfetch = self.cur.fetchall()

                        if self.sqlfetch:
                            self.Search("DublinCore", vuid=set(itertools.chain.from_iterable(self.sqlfetch)))
            else:
                self.cur.execute('''select vuid from DublinCore''')
                self.sqlfetch = self.cur.fetchall()

                if self.sqlfetch:
                    self.Search("DublinCore", vuid=set(itertools.chain.from_iterable(self.sqlfetch)))
            # flatten the nested list
            #self.data_fetchall = list(itertools.chain.from_iterable(self.data_fetchall))
            #for self.value in self.data_fetchall:




        elif self.database == "FilePathByFormat":

            if self.vuid and self.data:
                self.data_fetchall = []
                for self.key, self.v in self.data.items():
                    for self.value in self.v:
                        self.sql = (self.vuid, self.value)

                        self.cur.execute('''select * from FilePathByFormat where vuid=? and codec=?''', self.sql)
            elif self.vuid:
                self.tuple = (self.vuid,)
                self.cur.execute('''select * from FilePathByFormat where vuid=?''', self.tuple)
                self.data_fetchall = self.cur.fetchall()

            elif self.data:
                self.data_fetchall = []
                for self.key, self.v in self.data.items():
                    for self.value in self.v:
                        self.sql = (self.value,)
                        self.cur.execute('''select * from FilePathByFormat where codec=?''', self.sql)
                        self.data_fetchall.append(self.cur.fetchall())
            else:
                self.cur.execute('''select * from FilePathByFormat''')
                self.data_fetchall = self.cur.fetchall()

            self.data_fetchall = list(itertools.chain.from_iterable(self.data_fetchall))
            print(self.data_fetchall)
        self.con.close()



the_object = MetaHandler()

a = 2

if a == 1:
    dict = {"codec": ("ffv1",)}
    the_object.Search("FilePathByFormat", data=dict, vuid=10)
    # output [[(10, 'ffv1', '/this/is/a/path')]]
elif a == 2:
    dict = {"title": ("once upon a time...", "the Title")}
    the_object.Search("DublinCore", data=dict)
    # output [(16, 'actor', 'mario'), (16, 'actor', 'the hand')]
elif a == 3:
    dict = {"actor": ("mario", "the hand"), "director":("poulain", "Jo"), "title": ("the title",)}
    the_object.New("DublinCore", dict)