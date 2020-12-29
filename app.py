import streamlit as st
import pandas as pd

st.set_page_config(layout='wide')
import plotly.express as px

st.title('TerraELO Web App')


@st.cache(show_spinner=False, persist=True)  # save computation between reruns
def get_full_df():
    with st.spinner('Loading excel spreadsheet...'):  # show a progress meter
        full_df = pd.read_excel('poore_nemecek_supplement_spreadsheet.xlsx', sheet_name=1,
                                header=2)
    return full_df


full_df = get_full_df()

# Get Row Ranges for Commodities
rows = full_df[full_df.iloc[:, 0].notna()].iloc[:, 1]

commodity_rows = {
    commodity: (start, end)
    for start, end, commodity in zip(rows.index, rows.index[1:], rows)
}

# Select the commodity to analyze
commodity = st.selectbox(label='Commodity', options=list(commodity_rows.keys()))
start, end = commodity_rows[commodity]
df_filtered = full_df[start:end].dropna(axis=0, subset=['Product'])

numerical_cols = ['Land Use (m2*yr)', 'GHG Emis \n(kg CO2 eq)', 'Freshwtr. Withdr. (L)']

with st.beta_expander('Country Analysis'):
    st.markdown('This tool analyzes a column as a function of the country.')
    col = st.selectbox(label='Column to Analyze', options=numerical_cols)

    df_filtered[col] = df_filtered[col].replace(',', '', regex=True).astype(float)  # remove commas
    data = df_filtered.groupby('Country')[col].mean()

    fig = px.bar(x=data.index, y=data, title=f'{col} vs. Country for {commodity}',
                 labels={'x': 'Country', 'y': col}, width=1500, height=600)
    st.plotly_chart(fig)

    fig = px.scatter_geo(size=data, locations=data.index, locationmode='country names',
                         title=f'{col} for {commodity}', labels={'locations': 'Country', 'size': col}, width=1500,
                         height=600)
    st.plotly_chart(fig)
