# app.py

import streamlit as st
from datetime import datetime
import pytz
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
import sqlite3
import csv

from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# Initialize Streamlit app
st.title('Transactions Dashboard')

# Define LLM class and instantiate llm object
class LLM:
    def __init__(self):
        my_credentials = {
            "url": "https://us-south.ml.cloud.ibm.com",
            "apikey": "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U"
        }

        params = {
            GenParams.MAX_NEW_TOKENS: 1000,
            GenParams.TEMPERATURE: 0.1,
        }

        LLAMA2_model = Model(
            model_id='meta-llama/llama-2-70b-chat',
            credentials=my_credentials,
            params=params,
            project_id="16acfdcc-378f-4268-a2f4-ba04ca7eca08",
        )

        self.llm = WatsonxLLM(LLAMA2_model)

llm_object = LLM()
llm = llm_object.llm

# Initialize SQLDatabase instance
db = SQLDatabase.from_uri("sqlite:///history.db")

# Function to connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('history.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database and populate with initial data
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Category TEXT,
            CustomerName TEXT,
            CustomerNumber TEXT,
            InvoiceNumber TEXT,
            InvoiceAmount INTEGER,
            InvoiceDate DATE,
            DueDate DATE,
            ForecastCode TEXT,
            ForecastDate DATE,
            Collector TEXT
        );
    """)

    if conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 0:
        with open('transactions.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            sample_data = list(reader)
            conn.executemany('INSERT INTO transactions (Category, CustomerName, CustomerNumber, InvoiceNumber, InvoiceAmount, InvoiceDate, DueDate, ForecastCode, ForecastDate, Collector) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', sample_data)

    conn.commit()
    conn.close()

init_db()

# Initialize SQLDatabaseChain instance
db_chain = SQLDatabaseChain(llm, db, verbose=True)

# Function to fetch transactions from database
def fetch_transactions():
    conn = get_db_connection()
    cursor = conn.execute('SELECT id, * FROM transactions ORDER BY InvoiceDate DESC')
    transactions = [dict(ix) for ix in cursor.fetchall()]
    conn.close()
    return transactions

# Main function to handle inquiry submission
def handle_inquiry(inquiry):
    prompt = f"""
    <<SYS>>
    You are a powerful text-to-SQLite model, and your role is to answer questions about a database. You are given questions and context regarding the Invoice details table, which represents the detailed records of currently open invoices.
    The table name is transactions and corresponding columns are id, *.
    You must run SQLite queries to the table to find an answer. Ensure your query does not include any non-SQLite syntax such as DATE_TRUNC or any use of backticks (`) or "```sql". Then, execute this query against the 'transactions' table and provide the answer.

    Guidelines:
    - Filter results using the current time zone: {datetime.now(pytz.timezone('America/New_York'))} only when query specifis a specific date/time period. You should use ">=" or "<=" operators to filter the date or use "GROUP BY strftime('%m', date)" for grouping into month.  Assume the date format in the database is 'YYYY-MM-DD'.
    - If the query result is [(None,)], run the SQLite query again to double check the answer.
    - If a specific category is mentioned in the inquiry, such as 'Yellow', 'Red', or 'Green', use the "WHERE" condition in your SQL query to filter transactions by that category. For example, when asked for the complete invoice details for 'Green', use "FROM transactions WHERE category = 'Green'".
    - If not asked for a specific category, you shouldn't filter any category out. On the other hand, you should use "where" condition to do the filtering. When asked for the average amount in a category, use the SQLite query (AVG(amount) WHERE category = 'category_name').
    - When asked for \'highest\' or \'lowest\', use SQL function MAX() or MIN() respectively.
    - If a specific condition is provided in the inquiry, such as mentioning a specific Collector like 'John', 'David', 'Lisa', 'Mary', or 'Michael', and specifying a category such as 'Yellow', 'Red', or 'Green', use the "WHERE" clause in your SQL query to filter transactions accordingly. For example, if you need to fetch invoice details for 'John' and 'Green', you would use "FROM transactions WHERE Collector = 'John' AND category = 'Green'".

    Use the following format to answer the inquiry:

    Response: Result of the SQLite-compatible SQL query. If you know the transaction details such as the Category, Customer Name, Customer #, Inv. #, Inv. Amt, Inv. Date, Due Date, Forecast Code, Forecast Date, and Collector, mention it in your answer to be more clear.
    ---------------------- line break
    <br>
    ---------------------- line break
    <br>
    Explanation: Concise and succinct explanation on your thought process on how to get the final answer including the relevant transaction details such as the Category, Customer Name, Customer #, Inv. #, Inv. Amt, Inv. Date, Due Date, Forecast Code, Forecast Date, and Collector.
    ---------------------- line break
    <br>
    ---------------------- line break
    <br>
    Advice: Provide tips here, such as reminding users of progress for invoices with a due date within 10 days by comparing the due date with today.

    <</SYS>>

    {inquiry}
    """
    response = db_chain.run(prompt)

    response = response.replace('\n', '<br>')

    return response

# Streamlit UI components
inquiry = st.text_area('Enter your inquiry:')
if st.button('Submit'):
    response = handle_inquiry(inquiry)
    st.markdown(f"**Response:** {response}")

# Display transactions
transactions = fetch_transactions()
st.write('Recent Transactions:')
st.write(transactions)
