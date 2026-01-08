import openai

import pandas as pd
import sqlite3
import streamlit as st

client = openai.OpenAI()
openai.api_key = st.secrets["OPENAI_API_KEY"]

OPENAI_MODEL = "gpt-3.5-turbo"

# Function to return the database file as a string
def load_sql_file_to_string(filepath):
    try:
        with open(filepath, 'r', encoding='latin-1') as file: # latin-1
            sql_content = file.read()
        return sql_content

    except Exception as e:
        print(f"error while reading file: {e}")
        return None

# Let's create an SQL Generation Function
def generate_sql_query(user_query, db_schema):    
    # Generates a SQL query from a natural language query using OpenAI's API.
    try:
        # Construct the system message. This sets the role and behavior of the AI.
        # It tells the AI to act as a MySQL SQL generator and provides the database schema.
        system_message = {
            "role": "system",
            "content": (
                "You are a very helpful assistant that translates natural language questions "
                "into MySQL SQL queries. "
                "You are given the following database schema:\n\n"
                f"{db_schema}\n\n"
                "Your task is to generate the correct SQL query for the user's question. "
                "Only return the SQL query, without any additional text or explanations."
                "Do not include ```sql or any other markdown formatting."
            )
        }

        # Construct the user message. This contains the actual question from the user.
        user_message = {
            "role": "user",
            "content": user_query,
        }

        # Make the API call to OpenAI.
        # We use chat.completions.create as it's designed for conversational models.
        response = client.chat.completions.create(
            model=OPENAI_MODEL,  # Specify the model to use.
            messages=[
                system_message,  # Provide the system instructions and schema.
                user_message,    # Provide the user's natural language query.
            ],
            temperature=0.0,     # Set temperature to 0 for deterministic and factual SQL generation.
            max_tokens=500,      # Limit the length of the generated SQL query.
            stop=["--", ";"],    # Stop generation if these tokens are encountered, useful for SQL.
                                 # Note: The AI might still include these, so post-processing might be needed.
        )

        # Extract the generated SQL query from the response.
        # The response structure is typically response.choices[0].message.content.
        sql_query = response.choices[0].message.content.strip()

        # Simple post-processing to ensure clean SQL output.
        # Remove any leading/trailing backticks or 'sql' tags that the AI might sometimes add.
        if sql_query.startswith("```sql"):
            sql_query = sql_query[len("```sql"):].strip()
        if sql_query.endswith("```"):
            sql_query = sql_query[:-len("```")].strip()

        return sql_query

    except openai.APIError as e:
        # Handle API errors (e.g., invalid API key, rate limits).
        return f"OpenAI API Error: {e}"
    except Exception as e:
        # Handle any other unexpected errors.
        return f"An unexpected error occurred: {e}"
#####################################################################################    
st.title("SQL Solver",text_alignment="center")

with st.form(key='submit_csv'):
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    user_query = st.text_area("Enter your SQL query: ")
    submit_button = st.form_submit_button(label='SQL Solver')

if submit_button:
    if uploaded_file and user_query:
        df = pd.read_csv(uploaded_file)
        db_file = 'database.sql'
        table_name = 'tableQ'

        # Connect to the SQLite database (it will be created if it doesn't exist)
        conn = sqlite3.connect(db_file)

        df.to_sql(table_name, conn, if_exists='replace', index=False)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()    
    
        db_schema = load_sql_file_to_string(db_file)    
        st.write(generate_sql_query(user_query, db_schema))
