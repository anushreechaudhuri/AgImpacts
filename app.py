import streamlit as st
import pandas as pd

st.set_page_config(layout='wide')
import plotly.express as px

st.title('Welcome to the AgImpacts Interactive Web Tool!')


@st.cache(show_spinner=False, persist=True)  # save computation between reruns
def get_full_df():
    with st.spinner('Loading excel spreadsheet...'):  # show a progress meter
        full_df = pd.read_excel('Terrafrosh_All_Commodity_Data.xlsx', sheet_name=1,
                                header=1)
    return full_df


full_df = get_full_df()

# Get Row Ranges for Commodities
rows = full_df[full_df.iloc[:, 0].notna()].iloc[:, 1]

commodity_rows = {
    commodity: (start, end)
    for start, end, commodity in zip(rows.index, rows.index[1:], rows)
}

# Select the commodity to analyze
commodity = st.sidebar.selectbox(label='Commodity', options=list(commodity_rows.keys()))
start, end = commodity_rows[commodity]
df_filtered = full_df[start:end].dropna(axis=0, subset=['Reference'])

numerical_cols = ['Land Use (m^2*year)', 'GHG Emissions (kg CO2 eq)', 'Freshwater Withdrawal (L)', 
'Acidifying Emissions (kg SO2 eq)', 'Eutrophying Emissions (kg PO4 eq)']

col_labels = [  # Tuples of (column name, pretty print name for axis labels)
('Land Use (m^2*year)','Land Use (m<sup>2</sup>*yr)'), ('GHG Emissions (kg CO2 eq)', 'GHG Emissions (kg CO2 eq) '),
('Freshwater Withdrawal (L)', 'Freshwater Withdrawal (L)'),
('Eutrophying Emissions (kg PO4 eq)', 'Eutrophication Potential (kg PO<sub>4</sub><sup>3-</sup> eq)'),
('Acidifying Emissions (kg SO2 eq)', 'Acidification Potential (kg SO<sub>2</sub> eq)')]

indicators = ['Land Use (m^2*year)', 'Freshwater Withdrawal (L)', 
'Acidifying Emissions (kg SO2 eq)', 'Eutrophying Emissions (kg PO4 eq)']

with st.beta_expander('Geographic Overview of Indicators'):
    st.markdown('This tool analyzes a column as a function of the country.')
    col = st.selectbox(label='Column to Analyze', options=numerical_cols)

    df_filtered[col] = df_filtered[col].replace(',', '', regex=True).replace('-', '', regex=True).replace('%', '', regex=True).replace(' ', '', regex=True).replace('', 'NaN').astype(float)  # remove commas
    data = df_filtered.groupby('Country')[col].mean()

    fig = px.bar(x=data.index, y=data, title=f'{col} vs. Country for {commodity}',
                 labels={'x': 'Country', 'y': col}, width=1500, height=600)
    st.plotly_chart(fig)

    fig = px.scatter_geo(size=data.fillna(0), locations=data.index, locationmode='country names',
                         title=f'{col} for {commodity}', labels={'locations': 'Country', 'size': col}, width=1500,
                         height=600)
    st.plotly_chart(fig)
with st.beta_expander('See Raw Data'):
    st.dataframe(df_filtered)

ghg = 'GHG Emissions (kg CO2 eq)'
with st.beta_expander('Impact Analysis (Work in Progress)'):
    quantile_list = df_filtered[ghg].quantile([0.25,0.5,0.75, 1.0])
    quantile_list = pd.DataFrame(quantile_list)
    quartile_titles = ['Q1', 'Q2', 'Q3','Q4']
    quantile_list['Quart Titles'] = quartile_titles
    st.write(quantile_list)
    q1 = st.checkbox('Quartile 1 of Producer GHG Emissions (0-25%)')
    q2 = st.checkbox('Quartile 2 of Producer GHG Emissions (25-50%)')
    q3 = st.checkbox('Quartile 3 of Producer GHG Emissions (50-75%)')
    q3 = st.checkbox('Quartile 4 of Producer GHG Emissions (75-100%)')
    if q1:
        for indicator in indicators:
            y_axis = [indicator]
            df_filtered[indicator] = df_filtered[indicator].replace(',', '', regex=True).replace('-', '', regex=True).replace('%', '', regex=True).replace(' ', '', regex=True).replace('', 'NaN').astype(float)  # remove commas
            average = [df_filtered[indicator].mean()]
            fig = px.bar(x=average, y=y_axis,
                 labels={'x': 'Value'}, template = 'simple_white', orientation='h')
            st.plotly_chart(fig)



    

    
