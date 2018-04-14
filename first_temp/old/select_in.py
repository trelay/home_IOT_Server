#!/usr/bin/env python

import sqlite3
conn = sqlite3.connect('Temp.db')
c = conn.cursor()
c.execute('SELECT * FROM temp_in')

out= c.fetchall()
print len(out)
for value in out:
    print(value)
conn.close()
