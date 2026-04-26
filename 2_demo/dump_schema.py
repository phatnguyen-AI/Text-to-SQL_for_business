import os
import sqlalchemy
import pandas as pd
from urllib.parse import quote_plus

DB_SERVER='localhost'
DB_PORT='1434'
DB_USER='sa'
DB_PASSWORD='YourStrong@Passw0rd'
DB_NAME='BusinessDB'
pwd_encoded = quote_plus(DB_PASSWORD)
driver = 'ODBC+Driver+18+for+SQL+Server'
conn_str = f'mssql+pyodbc://{DB_USER}:{pwd_encoded}@{DB_SERVER},{DB_PORT}/{DB_NAME}?driver={driver}&TrustServerCertificate=yes&Encrypt=no'
engine = sqlalchemy.create_engine(conn_str)
schema = ''
tables = pd.read_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'", engine)
for _, row in tables.iterrows():
    tbl = row['TABLE_NAME']
    schema += f'Table: {tbl}\nColumns:\n'
    cols = pd.read_sql(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{tbl}'", engine)
    for _, col in cols.iterrows():
        schema += f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})\n"
    schema += '\n'
print(schema)
