#!/usr/bin/env python

import sqlite3
conn = sqlite3.connect('Temp.db')
c = conn.cursor()
c.execute('SELECT * FROM temp_out')
values =c.fetchall()
conn.close()

temp_array=[]
for value in values:
    try:
        temp_array.append(float(value[1]))
    except ValueError:
        pass
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.plot(temp_array)
plt.savefig("./static/txt.png")
