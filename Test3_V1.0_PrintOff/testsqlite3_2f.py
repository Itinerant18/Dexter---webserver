
#https://www.digitalocean.com/community/tutorials/how-to-use-the-sqlite3-module-in-python-3
#cur.execute("insert into contacts (name, phone, email) values (?, ?, ?)", (name, phone, email))

#https://www.geeksforgeeks.org/how-to-count-the-number-of-rows-of-a-given-sqlite-table-using-python/
#https://www.tutorialspoint.com/how-to-count-the-number-of-rows-of-a-given-sqlite-table-using-python

import sqlite3
import random
#import pandas as pd

#Connect to Database
connection = sqlite3.connect("dexterpanel2.db")
print(connection.total_changes)

cursor = connection.cursor()
#Create Database
#try:
#    cursor = connection.cursor()
#    cursor.execute("CREATE TABLE systemLogs (deviceType TEXT, logType TEXT, rtcYear INTEGER, rtcMonth INTEGER, rtcDate INTEGER, rtcHour INTEGER, rtcMinute INTEGER, rtcSecound INTEGER)")
#except:
#  print("table already exists")

rows = cursor.execute("SELECT deviceType, logType, rtcYear, rtcMonth, rtcDate, rtcHour, rtcMinute, rtcSecound  FROM systemLogs").fetchall()
#print(rows)
response = rows
 
print("Count of Logs") 
cursor.execute("SELECT * FROM systemLogs")
totalLogs = len(cursor.fetchall())
#print(len(cursor.fetchall()))
print(totalLogs)

x = 0
x = int(totalLogs)

print(x) 

y = 0
for y in range(x):
  print(response[y])


rows = cursor.execute("SELECT deviceType, logType, rtcYear, rtcMonth, rtcDate, rtcHour, rtcMinute, rtcSecound  FROM systemLogs").fetchall()
#print(rows)
response = rows
#print(response)
print("Count of Rows") 
cursor.execute("SELECT * FROM systemLogs")
totalLogs = len(cursor.fetchall())
#print(len(cursor.fetchall()))
print(totalLogs)

x = 0
x = int(totalLogs)

print(x) 

y = 0
for y in range(x):
  print(response[y])


cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "BACS"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('BACS') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "BACS"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])





cursor.execute('SELECT * FROM systemLogs WHERE rtcDate = "1"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('DATE') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE rtcDate = "1"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])




cursor.execute('SELECT * FROM systemLogs WHERE rtcHour >= "15"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('HOUR') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE rtcHour >= "15"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])



cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "CCTV"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('CCTV') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "CCTV"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])


cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "FAS"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('FAS') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "FAS"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])


cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "BAS"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('BAS') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "BAS"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])


cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "TIME_LOCK"', )
#output = cursor.fetchall()
totalLogs = len(cursor.fetchall())
#print(*output, sep="\n")
#print(output)
print(totalLogs)

x = 0
x = int(totalLogs)
print('TIME_LOCK') 
print(x) 

#y = 0
#for y in range(x):
#  print(response[y])


data = cursor.execute('SELECT * FROM systemLogs WHERE deviceType = "TIME_LOCK"', )
output = data.fetchall()
#print(output)

y = 0
for y in range(x):
  print(output[y])


connection.close()


try:
    if response:
        #print(response[0])
        #print(response[1])
        response2 = str(response)
        #print(response2)
        response3 = response2.split(",")
        #print(response3)
        #print(response3[0])
        #print(response3[1])

except Exception:
    pass





