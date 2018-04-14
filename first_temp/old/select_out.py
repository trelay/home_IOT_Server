#!/usr/bin/env python

import sqlite3
conn = sqlite3.connect('Temp.db')
c = conn.cursor()
c.execute('SELECT * FROM temp_out')
#c.execute("SELECT * FROM temp_out ORDER BY ID DESC LIMIT 1")
#c.execute("select * from temp_out where temp='Start'")
#c.execute("select * from temp_out limit 0,10")

for value in c.fetchall():
    print(value)
#data=c.fetchall()
#print type(data)
#print data
conn.close()
