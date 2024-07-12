import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from langchain_experimental.sql import SQLDatabaseChain
from langchain.utilities import SQLDatabase  # 추가된 import

# WatsonxLLM Model Configuration
my_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U"  # Replace with your actual API key
}

params = {
    GenParams.MAX_NEW_TOKENS: 1000,
    GenParams.TEMPERATURE: 0.1,
}

LLAMA2_model = Model(
    model_id='meta-llama/llama-2-70b-chat',
    credentials=my_credentials,
    params=params,
    project_id="16acfdcc-378f-4268-a2f4-ba04ca7eca08"  # Replace with your actual project ID
)

llm = WatsonxLLM(LLAMA2_model)

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('history.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Streamlit application
st.title('Transactions Dashboard')

# Initialize the SQLDatabase object and run init_db() to set up the database
db = SQLDatabase.from_uri("sqlite:///history.db")
db.init_db()

# Initialize SQLDatabaseChain with WatsonxLLM and SQLDatabase objects
db_chain = SQLDatabaseChain(llm, db, verbose=True)

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
