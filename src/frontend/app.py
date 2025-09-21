import streamlit as st
import sqlite3
import pandas as pd

st.title("Sedinte din Camera Deputatilor")

conn = sqlite3.connect("data/db.sqlite")
df = pd.read_sql_query("SELECT * FROM speeches LIMIT 100;", conn)
conn.close()

st.dataframe(df)
