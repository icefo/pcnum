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
                self.data_fetchall = []
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
            elif self.vuid or self.vuid == 0:
                self.data_fetchall = {}
                self.tuple = (self.vuid,)
                self.cur.execute('''select * from DublinCore where vuid=?''', self.tuple)
                for self.tuplevalue in self.cur.fetchall():
                    try:
                        self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]].append(self.tuplevalue[2])
                    except KeyError:
                        self.data_fetchall[self.tuplevalue[0]] = {}
                        self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]] = [self.tuplevalue[2]]

            elif self.data:
                self.data_fetchall = {}
                for self.key, self.v in self.data.items():
                    if self.v:
                        for self.value in self.v:
                            self.sql = (self.key, self.value)

                            self.cur.execute('''select * from DublinCore where subject=? and object=?''', self.sql)
                            self.sqlfetch = self.cur.fetchall()
                            #print(self.sqlfetch)
                            if self.sqlfetch:
                                for self.tuplevalue in self.sqlfetch:
                                    self.Search("DublinCore", vuid=self.tuplevalue[0])

                    else:
                        self.sql = (self.key,)

                        self.cur.execute('''select * from DublinCore where subject=?''', self.sql)
                        self.sqlfetch = self.cur.fetchall()
                        if self.sqlfetch:
                            for self.tuplevalue in self.sqlfetch:
                                try:
                                    self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]].append(self.tuplevalue[2])
                                except KeyError:
                                    self.data_fetchall[self.tuplevalue[0]] = {}
                                    self.data_fetchall[self.tuplevalue[0]][self.tuplevalue[1]] = [self.tuplevalue[2]]
            else:
                self.cur.execute('''select * from DublinCore''')
                self.data_fetchall = self.cur.fetchall()
            # flatten the nested list
            #self.data_fetchall = list(itertools.chain.from_iterable(self.data_fetchall))
            #for self.value in self.data_fetchall:

            print(self.data_fetchall)


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