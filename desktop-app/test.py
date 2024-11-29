import sqlite3
from tabulate import tabulate  # Optional, for better table formatting

# Path to your SQLite database file
db_path = "app-data.db"

# Connect to the SQLite database
conn = sqlite3.connect(db_path)

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Fetch all rows from the 'suggestions' table
cursor.execute("SELECT * FROM suggestions")
rows = cursor.fetchall()

# Print the rows
print("Database Contents:")
if rows:
    print(tabulate(rows, headers=["ID", "Content", "Timestamp"], tablefmt="pretty"))
else:
    print("No data found in the 'suggestions' table.")

# Close the connection
conn.close()
