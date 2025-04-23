import sqlite3
import os
print(os.path.exists("./instance/database.db"))
# Connect to your database
conn = sqlite3.connect("./instance/database.db")
cursor = conn.cursor()

# Query the data
cursor.execute(
    'SELECT slitem.ingredient, slitem.measure, mitem.amount FROM Shoppinglistitem as slitem JOIN Menuitem as mitem ON slitem.menuitem_id = mitem.id'
    )
rows = cursor.fetchall()

# Print the data
for row in rows:
    print(row)
print(cursor.description)
# Close the connection
conn.close()