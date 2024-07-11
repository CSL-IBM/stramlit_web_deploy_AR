import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from langchain_experimental.sql import SQLDatabaseChain
from streamlit_web_deploy_AR.model import llm

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Creating the Prompt Template
QUERY = """
<<SYS>> 
You are a powerful text-to-SQLite model, and your role is to answer questions about a database. You are given questions and context regarding the Invoice details table, which represents the detailed records of currently open invoices.
The table name is {table_name} and corresponding columns are {columns}.
You must run SQLite queries to the table to find an answer. Ensure your query does not include any non-SQLite syntax such as DATE_TRUNC or any use of backticks (`) or "```sql". Then, execute this query against the 'transactions' table and provide the answer.

Guidelines:
- Filter results using the current time zone: {time} only when query specifis a specific date/time period. You should use ">=" or "<=" operators to filter the date or use "GROUP BY strftime('%m', date)" for grouping into month.  Assume the date format in the database is 'YYYY-MM-DD'.
- If the query result is [(None,)], run the SQLite query again to double check the answer. 
- If a specific category is mentioned in the inquiry, such as 'Yellow', 'Red', or 'Green', use the "WHERE" condition in your SQL query to filter transactions by that category. For example, when asked for the complete invoice details for 'Green', use "FROM transactions WHERE category = 'Green'".
- If not asked for a specific category, you shouldn't filter any category out. On the other hand, you should use "where" condition to do the filtering. When asked for the average amount in a category, use the SQLite query (AVG(amount) WHERE category = 'category_name').
- When asked for \'highest\' or \'lowest\', use SQL function MAX() or MIN() respectively.
-If a specific condition is provided in the inquiry, such as mentioning a specific Collector like 'John', 'David', 'Lisa', 'Mary', or 'Michael', and specifying a category such as 'Yellow', 'Red', or 'Green', use the "WHERE" clause in your SQL query to filter transactions accordingly. For example, if you need to fetch invoice details for 'John' and 'Green', you would use "FROM transactions WHERE Collector = 'John' AND category = 'Green'".

Use the following format to answer the inquiry:

Response: Result of the SQLite-compatible SQL query. If you know the transaction details such as the Category,  Customer Name, Customer #, Inv. #, Inv. Amt, Inv. Date, Due Date, Forecast Code, Forecast Date, and Collector, mention it in your answer to be more clear.
---------------------- line break
<br>
---------------------- line break
<br>
Explanation: Concise and succinct explanation on your thought process on how to get the final answer including the relevant transaction details such as the Category,   Customer Name, Customer #, Inv. #, Inv. Amt, Inv. Date, Due Date, Forecast Code, Forecast Date, and Collector.
---------------------- line break
<br>
---------------------- line break
<br>
Advice: Provide tips here, such as reminding users of progress for invoices with a due date within 10 days by comparing the due date with today.

<</SYS>>

[INST] 
{inquiry}
[/INST]
"""

# Initialize the Database Chain
db = get_db_connection()
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)

# Streamlit application
st.title('Transactions Dashboard')

# Displaying transactions
conn = get_db_connection()
transactions = conn.execute('SELECT id, * FROM transactions ORDER BY InvoiceDate DESC').fetchall()
conn.close()

st.subheader('Recent Transactions')
if transactions:
    for transaction in transactions:
        st.write(f"ID: {transaction['id']}, Date: {transaction['InvoiceDate']}, Other details: ...")
else:
    st.write('No transactions found.')

# Handling user inquiries
st.subheader('Ask a question about the database')
inquiry = st.text_area("Enter your inquiry here:")

if st.button('Submit'):
    current_time = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
    response = QUERY.format(
        table_name='transactions',
        columns='id, category, customer_name, customer_id, invoice_number, amount, invoice_date, due_date, forecast_code, forecast_date, collector',
        time=current_time,
        inquiry=inquiry
    )
    result = db_chain.run(response)
    st.write(result)

