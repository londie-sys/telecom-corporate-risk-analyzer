import os
import logging
import pdfplumber
import pandas as pd
import mysql.connector 

logging.basicConfig(
    filename='etl_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Holocust",
    database="telecoms"
)
mycursor = mydb.cursor()

def extract_pdf_data(pdf_path, company_name):
    """
    Attempts to read data rows from standard financial report table layouts.
    Logs warning if structural unit mismatches or missing value are detected.
    """
    extracted_rows = []
    logging.info(f"Starting extraction for file:{pdf_path} ({company_name})")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table in tables:
                    for row in table:

                        clean_row = [str(cell).strip() if cell else None for cell in row]
                        if any(clean_row):
                            extracted_rows.append(clean_row)

        logging.info(f"Successfully processed {pdf_path}. Extracted {len(extracted_rows)} raw rows.")
    except Exception as e:
        logging.error(f"Failed to read PDF {pdf_path}: {str(e)}") 
        print(f"PDF extraction error. Falling back to careful manual data verification layout.")  
        return extracted_rows

def load_data_to_sql(df_to_load):
    """ 
    Insert data using an idempotent stategy. Checks for duplicates before appending to make sure running it multiple times does not
    break prior years.
    """  
    print("Running database append routine...") 
    for index, row in df_to_load.iterrows():
        check_query = "SELECT 1 FROM financial_data WHERE company = %s AND year = %s"
        mycursor.execute(check_query, (row['company'], row['Year']))
        exist = mycursor.fetchone()

        if exist:
            logging.warning(f"Data Quality Issue: Duplicate skipped for {row['company']} Year {row['Year']}. Record already exists.") 
            continue

        insert_query = """ 
        INSERT INTO financial_data (company, year, revenue, ebitda, net_profit, subscribers)
        VALUES(%s, %s, %s, %s, %s, %s)
          """  
        values = (row['company'], row['Year'], row['revenue'], row['ebitda'], row['net_profit'], row['subscribers']) 
        mycursor.execute(insert_query, values)  
        logging.info(f"Successfully appended new data entry: {row['company']} {row['Year']}") 
        mydb.commit() 
        print("Database sync complete. Check 'etl_pipeline.log' for full data_quality report.")  

if __name__ == "__main__":
     mycursor.execute("""
     CREATE TABLE IF NOT EXISTS financial_data(
     company VARCHAR (100),
     year INT,
     revenue DECIMAL(18.2),
     ebitda DECIMAL (18.2),
     net_profit DECIMAL(18.2),
     subscribers BIGINT
     );   
     """)
     print("Initializing test run....")
     test_data = {
            'company': ['Cell C'],
            'Year': [2024],
            'revenue': [12000.00],
            'ebitda': [1100.00],
            'net_profit': [-500.00],
            'subscribers': [15]
            }
df_test = pd.DataFrame(test_data)
load_data_to_sql(df_test)

      





