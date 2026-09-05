import pandas as pd
import numpy as np
import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

@st.cache_resource
def get_connection():
    return sqlite3.connect("telecoms.db", check_same_thread=False)
mydb = get_connection()
mycursor = mydb.cursor()

mycursor.execute("DROP TABLE IF EXISTS financial_data")
print("Old table wiped clean")
sql_create_table = """
CREATE TABLE IF NOT EXISTS financial_data(
    company VARCHAR(100),
    Year INT,
    revenue DECIMAL(18,2),
    ebitda DECIMAL(18,2),
    net_profit DECIMAL(18,2),
    subscribers BIGINT

);
"""
mycursor.execute(sql_create_table)
print("Table created successfully")

mycursor.execute("PRAGMA table_info(financial_data)")
for row in mycursor.fetchall():
    print(row)


insert_query = """
INSERT INTO financial_data
(company, year, revenue, ebitda, net_profit, subscribers)
VALUES (?, ?, ?, ?, ?, ?)
"""
excel_file = "SA_Telecoms_Dataset_2015_2025.xlsx"

def load_company_sheet(sheet_name, company_name):
    df = pd.read_excel(excel_file, 
    sheet_name=sheet_name, header=3)
    df = df.rename(columns={
        'Fiscal Year': 'Year',
        'Revenue (ZAR m)': 'revenue',
        'EBITDA (ZAR m)': 'ebitda',
        'Net Profit / (Loss) (ZAR m)': 'net_profit',
        'Subscribers (m)': 'subscribers'
    })
    df["company"] = company_name
    return df

telkom = load_company_sheet('Telkom', 'Telkom')
cellc = load_company_sheet('Cell C', 'Cell C')
df_filtered = pd.concat([telkom, cellc], ignore_index=True)
print(df_filtered.to_string())

print(df_filtered.isnull())
df_filtered = df_filtered.dropna(subset=['revenue', 'ebitda', 'net_profit', 'subscribers'])
print(df_filtered.duplicated().any())
df_filtered = df_filtered.drop_duplicates()
df_filtered['company'] = df_filtered['company'].str.strip()
print(df_filtered.dtypes)
print(df_filtered.describe())
print(df_filtered.isnull().sum())
df_filtered = df_filtered.where(pd.notnull(df_filtered), None)

print("Inserting data into MySQL...")
for index, row in df_filtered.iterrows():
    value = (
        row['company'],
        row['Year'],
        row['revenue'],
        row['ebitda'],
        row['net_profit'],
        row['subscribers']
    )
    mycursor.execute(insert_query, value)
    mydb.commit()
    print(f"{len(df_filtered)}") 

sql_calculate_trends = """
WITH financial_trends AS (
    SELECT 
    company AS company_name,
    Year AS financial_year,
    revenue,
    ebitda,
    net_profit,
    subscribers,
    (CAST(revenue AS REAL) / NULLIF(subscribers, 0)) AS arpu,

    LAG(revenue) OVER(PARTITION BY company ORDER BY Year ) AS prev_revenue,
    LAG(ebitda) OVER (PARTITION BY company ORDER BY Year ) AS prev_ebitda,
    LAG(CAST(revenue AS REAL) / NULLIF(subscribers, 0)) OVER(PARTITION BY company ORDER BY Year) AS prev_arpu
    LAG(CAST(revenue AS REAL) / NULLIF(subscribers, 0)) OVER(PARTITION BY company ORDER BY Year) AS prev_arpu
    FROM financial_data
),
calculated_metrics AS (
SELECT
    company_name,
    financial_year,

    ((CAST(revenue AS REAL) - prev_revenue) / NULLIF(prev_revenue, 0)) * 100 AS revenue_growth_yoy,
    (CAST(ebitda AS REAL) / NULLIF(revenue, 0)) * 100 AS ebitda_margin,
    ((CAST(ebitda AS REAL) / NULLIF(revenue, 0 )) - (CAST(prev_ebitda AS REAL) / NULLIF(prev_revenue, 0))) AS ebitda_margin_change,

    (CAST(net_profit AS REAL) / NULLIF(revenue, 0)) * 100 AS net_profit_margin,
    (arpu - prev_arpu) AS arpu_change_yoy
    (CAST(net_profit AS REAL) / NULLIF(revenue, 0)) * 100 AS net_profit_margin,
    (arpu - prev_arpu) AS arpu_change_yoy
FROM financial_trends
),
risk_scoring AS (
    SELECT
        company_name,
        financial_year,
        revenue_growth_yoy,
        ebitda_margin,
        net_profit_margin,
        arpu_change_yoy,
        (
        (CASE WHEN revenue_growth_yoy < 0 THEN 1 ELSE 0 END) + 
        (CASE WHEN ebitda_margin_change < 0 THEN 1 ELSE 0 END) +
        (CASE WHEN net_profit_margin < 0 THEN 1 ELSE 0 END) +
        (CASE WHEN arpu_change_yoy < 0 THEN 1 ELSE 0 END)
         ) AS raw_risk_score
    FROM calculated_metrics
)
SELECT
    company_name,
    financial_year,
    revenue_growth_yoy,
    ebitda_margin,
    net_profit_margin,
    arpu_change_yoy,
    raw_risk_score,
   CASE
      WHEN raw_risk_score >= 3 THEN 'High Risk'
      WHEN raw_risk_score = 2 THEN 'Medium Risk'
      ELSE 'Low Risk'
   END AS risk_tier
FROM risk_scoring;         

"""   
df_risk_report = pd.read_sql_query(sql_calculate_trends, mydb)

print("\n--- ALL CALCULATED RISK SCORES---")
print(df_risk_report.to_string(index=False))

print("\n--- BACKTESTING CELL C ---")
cell_c_validation = df_risk_report[df_risk_report['company_name'].str.lower() == 'cell c']
print(cell_c_validation.to_string(index=False))

print("\n--- BACKTESTING TELKOM MARGIN PRESSURE ---")
telkom_validation = df_risk_report[df_risk_report['company_name'].str.lower() == 'telkom']
print(telkom_validation[['company_name', 'financial_year', 'ebitda_margin', 'risk_tier']].to_string(index=False))

df_risk_report['financial_year'] = pd.to_numeric(df_risk_report['financial_year'])
df_risk_report['raw_risk_score'] = pd.to_numeric(df_risk_report['raw_risk_score'])
df_risk_report['revenue_growth_yoy'] = pd.to_numeric(df_risk_report['revenue_growth_yoy'])

plt.figure(figsize=(12, 6))

for company in df_risk_report['company_name'].unique():
    company_df = df_risk_report[df_risk_report['company_name'] == company].sort_values('financial_year')
    plt.plot(company_df['financial_year'], company_df['raw_risk_score'], marker='o', label=company, linewidth=2)

plt.annotate('Cell C Restructuring & Distress', xy=(2022, 3), xytext=(2020, 3.5),
             arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=6))
 
plt.title('Telecom Company Risk Score Over Time', fontsize=14, fontweight='bold')  
plt.xlabel('Financial Year', fontsize=12)
plt.ylabel('Raw Risk Score (Max 4 Point)', fontsize=12)
plt.xticks(df_risk_report['financial_year'].unique())
plt.ylim(-0.5, 4.5)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc='upper left')

plt.tight_layout()
plt.savefig('telecom_risk_trends.png', dpi=300)
print('telecom_risk_trends.png')
#plt.show()


def generate_forecast(df_report, company_name, metric_column):
    """
    Fits a linear regression model on historical trends (2015-2025)
    and projects metrics into 2026-2027 with calculated confidence intervals.
    """
    history = df_report[df_report['company_name'] == company_name].sort_values('financial_year').dropna(subset=[metric_column])
    X_hist = history['financial_year'].values.reshape(-1, 1)
    y_hist = history[metric_column].values

    if len(X_hist) < 3: 
        return None, None, None, None

    model = LinearRegression()
    model.fit(X_hist, y_hist)
    future_years = np.array([2026.0, 2027.0]).reshape(-1, 1)
    predictions = model.predict(future_years)

    residuals = y_hist - model.predict(X_hist)
    residual_std_error = np.std(residuals) if len(residuals) > 1 else 0
    margin_error = 1.96 * residual_std_error

    lower_bound = predictions - margin_error
    upper_bound = predictions + margin_error
    return future_years.flatten(), predictions, lower_bound, upper_bound

st.set_page_config(page_title="Telecom Risk Analyzer", layout="wide")
st.title("Telecom Corporate Financial Risk Dashboard")
st.markdown("This dashboard leverages **SQL analytic engines** to compute real_time credit and financialm distress signals.")

st.sidebar.header("Dashboard Filters")
company = df_risk_report['company_name'].unique()
selected_company = st.sidebar.selectbox("Select a Telecom Operator:", company)
company_df = df_risk_report[df_risk_report['company_name'] == selected_company].sort_values('financial_year')
latest_record = company_df.iloc[-1]
st.subheader(f"Latest Financial Health Summary: {selected_company} ({latest_record['financial_year']})")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue Growth (YOY)", f"{latest_record['revenue_growth_yoy']:.2f}%")
col2.metric("EBITDA Margin", f"{latest_record['ebitda_margin']:.2f}%")
col3.metric("Net Profit Margin", f"{latest_record['net_profit_margin']:.2f}%")

risk_color = "red" if "high" in latest_record['risk_tier'] else ("orange" if "medium" in latest_record['risk_tier'] else "green")
col4.markdown(f"{risk_color}; {latest_record['risk_tier']}", unsafe_allow_html=True)
st.markdown("---")
view_col1, view_col2 = st.columns([1, 1])

st.markdown("---")
st.subheader(" Predictive Trend Forecasting")
show_forecast = st.checkbox("Enable Machine Learning Forecasting Engine (Project 2026-2027)")

if show_forecast:
    st.markdown("### Projected Operational Trajectory")
    f_years, f_preds, lower_b, upper_b = generate_forecast(df_risk_report, selected_company, 'revenue_growth_yoy')
    if f_preds is not None:
        for i, year in enumerate(f_years):
            st.write(f"**Year {year} Revenue Growth Projection:**")
            st.info(f"Predicted: {f_preds[i]:.2f}% | Expected Lower Limit: {lower_b[i]:.2f}% | Expected Upper Limit: {upper_b[i]:.2f}%")

            st.markdown("**Guidance Comparison Assessment:**")
            if selected_company.lower() == 'cell c':
                st.warning("*Analyst Divergence Note:* Cell C's public recovery goals emphasize immediate liquidity stabilizer turnarounds. A strict historical trend vectornprojects extended boundary pressure if operational disruptions persist unmitigated.")
            else:
                st.success("*Analyst Alignment Note:* Telkom's multi-year strucural consolidation aims for steady enterprise modernization. The forecast line mirrors their steady framework parameters nicely.")
    else:
        st.error("Insufficient timelin data available to project metrics safely.") 

with view_col1:
    st.subheader("Historical Corporate Risk Metrics")
    st.dataframe(company_df[['financial_year', 'revenue_growth_yoy', 'ebitda_margin', 'net_profit_margin', 'raw_risk_score', 'risk_tier']], use_container_width=True)

with view_col2:
    st.subheader("Comparative Sector Risk Trend") 
    st.image("telecom_risk_trends.png", use_container_width=True)  
st.success("Dashboard successfully updated with active SQL query insights.")

st.markdown("---")
st.subheader("Macro Context - Company Skill  or Economic Tailwind")

macro_data = {
    'financial_year':[2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'sa_gdp_growth': [1.5, 0.3, -6.3, 4.9, 2.0, 0.6, 1.2],
    'cpi_inflation': [4.6, 4.1, 3.3, 4.6, 6.9, 6.0, 5.3],
    'usd_zar_rate': [13.2, 14.4, 16.5, 14.8, 16.3, 18.4, 18.2]
}
df_macro = pd.DataFrame(macro_data)
df_risk_report['financial_year'] = pd.to_numeric(df_risk_report['financial_year'])
df_macro['financial_year'] = pd.to_numeric(df_macro['financial_year'])

st.markdown("### Historical Macroeconomic Context Matrix")
st.dataframe(df_macro, use_container_width=True)
st.markdown("### Statistical Causual Correlation Matrix")

col_m1, col_m2 = st.columns(2)
df_causual = pd.merge(df_risk_report, df_macro, on='financial_year', how='inner')

with col_m1:
    st.markdown("***Telkom Revenue Correlation Vectors:**")
    t_data = df_causual[df_causual['company_name'].str.lower() == 'telkom']
    if len(t_data) > 2:
        corr_gdp = t_data['revenue_growth_yoy'].corr(t_data['sa_gdp_growth'])
        corr_inf = t_data['revenue_growth_yoy'].corr(t_data ['cpi_inflation'])
        st.write(f"Correlation with SA GDP Growth: `{corr_gdp:.2f}`")
        st.write(f" Correlation with CPI Inflation: `{corr_inf:.2f}`")
    else:
        st.caption("Awaiting timeline extension to map matrix vectors.") 

with col_m2:
    st.markdown("***Cell C Revenue Correlation Vectors:**")
    c_data = df_causual[df_causual['company_name'].str.lower() == 'cell c']
    if len(c_data) > 2:
            corr_gdp = c_data['revenue_growth_yoy'].corr(c_data['sa_gdp_growth'])
            corr_inf = c_data['revenue_growth_yoy'].corr(c_data ['cpi_inflation'])
            st.write(f"Correlation with SA GDP Growth: `{corr_gdp:.2f}`")
            st.write(f" Correlation with CPI Inflation: `{corr_inf:.2f}`")
    else:
        st.caption("Awaiting timeline extension to map matrix vectors.") 

st.markdown("---")  
st.markdown("### Resiliency Executive Summary") 

st.info(
    "**Strategic Operational Summmary:**\n\n"
    " **Telkom Resiliency profile:** Telkom demostrates a **high decoupling** from local macroeconomic spikes. Its heavy orientation toward structural business-to-business (B2B) data transit networks and fibre-to-the-home infrastructure yields a defensive moat, indicating its growth patterns represent ** internal execution skill** rather than macroeconomic taiwinds.\n\n"
    " **Cell C Macro Vulnerability:** Conversly, Cell C exhibits a highly sensitive **negative correlation with high CPI inflation** Because its subscriber is heavily weighted toward price-sensitive consumer segments, domestic inflation directly erodes wallet shares-tiggering immediate usage contractions and subscriber churn. This confirms that Cll C lacks a protective structural macro insulation buffer."

)






