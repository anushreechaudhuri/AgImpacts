import streamlit as st
import pandas as pd

st.set_page_config(layout='wide')
import plotly.express as px

st.title('Welcome to the AgImpacts Interactive Web Tool!')
st.markdown('This is a work in progress. There are errors and unfinished portions for different commodities, but select Maize or Palm Oil to see a (mostly) working product.')

@st.cache(show_spinner=False, persist=True)  # save computation between reruns
def get_full_df():
    with st.spinner('Loading excel spreadsheet...'):  # show a progress meter
        full_df = pd.read_excel('Terrafrosh_All_Commodity_Data.xlsx', sheet_name=1,
                                header=1)
    return full_df

def format_col(df, col):
    df[col] = df[col].replace(',', '', regex=True).replace('-', '', regex=True).replace('%', '', regex=True).replace(' ', '', regex=True).replace('', 'NaN').astype(float)  # remove commas
    return df[col]

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
('Land Use (m^2*year)','Land Use (m<sup>2</sup>*yr)'),
('Freshwater Withdrawal (L)', 'Freshwater Withdrawal (L)'),
('Eutrophying Emissions (kg PO4 eq)', 'Eutrophication Potential (kg PO<sub>4</sub><sup>3-</sup> eq)'),
('Acidifying Emissions (kg SO2 eq)', 'Acidification Potential (kg SO<sub>2</sub> eq)')]

indicators = ['Land Use (m^2*year)', 'Freshwater Withdrawal (L)', 
'Acidifying Emissions (kg SO2 eq)', 'Eutrophying Emissions (kg PO4 eq)']

ghg = 'GHG Emissions (kg CO2 eq)'

with st.beta_expander('Indicator Graphs'):
    for y, name in col_labels:
        fig = px.scatter(x=df_filtered['GHG Emissions (kg CO2 eq)'],
                    template='simple_white',
            y=df_filtered[y],
            title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
            labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'System'}#, trendline = 'ols'
            )
        fig.update_layout(
        font_family="Calibri",
        font_color="black",
        title_font_family="Calibri",
        title_font_color="black",
        legend_title_font_color="black")
        fig.update_xaxes(title_font_family="Calibri")
        fig.update_yaxes(title_font_family="Calibri")
        #results = px.get_trendline_results(fig)
        #results = results.px_fit_results.iloc[0].summary()
        st.plotly_chart(fig)

with st.beta_expander('Impact Analysis'):
    cutoff = st.slider('Select a range of GHG emissions', min_value=df_filtered[ghg].min(), max_value=df_filtered[ghg].max())
    st.markdown(f'Your selected range is from {df_filtered[ghg].min()} (kg CO<sub>2</sub> eq) to {cutoff} (kg CO<sub>2</sub> eq).', unsafe_allow_html=True)
    cutoff_df = df_filtered.loc[df_filtered[ghg] <= cutoff, [ghg, 'Land Use (m^2*year)', 'Freshwater Withdrawal (L)', 
    'Acidifying Emissions (kg SO2 eq)', 'Eutrophying Emissions (kg PO4 eq)']]
    show_data = st.checkbox('Show Filtered Raw Data')
    show_quantiles = st.checkbox('Show Quantiles of GHG Emissions')
    if show_data:
        st.dataframe(cutoff_df)
    if show_quantiles:
            quantile_list = df_filtered[ghg].quantile([0.25,0.5,0.75, 1.0])
            quantile_list = pd.DataFrame(quantile_list)
            st.dataframe(quantile_list)
    for y, name in col_labels:
        cutoff_df[y] = format_col(cutoff_df, y)
        fig = px.scatter(x=cutoff_df['GHG Emissions (kg CO2 eq)'],
                    template='simple_white',
            y=cutoff_df[y],
            title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
            labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'System'}#, trendline = 'ols'
            )
        fig.update_layout(
        font_family="Calibri",
        font_color="black",
        title_font_family="Calibri",
        title_font_color="black",
        legend_title_font_color="black")
        fig.update_xaxes(title_font_family="Calibri")
        fig.update_yaxes(title_font_family="Calibri")
        #results = px.get_trendline_results(fig)
        #results = results.px_fit_results.iloc[0].summary()
        st.plotly_chart(fig)
        st.markdown(f'The median {name} for your selected range is {cutoff_df[y].median()}, and the average is {round(cutoff_df[y].mean(), 5)}.', unsafe_allow_html=True)

with st.beta_expander('Geographic Overview of Indicators'):
    st.markdown('This tool analyzes a column as a function of the country.')
    col = st.selectbox(label='Column to Analyze', options=numerical_cols)
    df_filtered[col] = format_col(df_filtered, col)
    data = df_filtered.groupby('Country')[col].mean()

    fig = px.bar(x=data.index, y=data, title=f'{col} vs. Country for {commodity}',
                 labels={'x': 'Country', 'y': col}, width=1500, height=600)
    st.plotly_chart(fig)

    fig = px.scatter_geo(size=data.fillna(0), locations=data.index, locationmode='country names',
                         title=f'{col} for {commodity}', labels={'locations': 'Country', 'size': col}, width=1500,
                         height=600)
    st.plotly_chart(fig)

with st.beta_expander('See Raw Data for Commodity'):
    st.markdown('[See the paper with original dataset here.](https://science.sciencemag.org/content/360/6392/987)', unsafe_allow_html=True)
    st.dataframe(df_filtered)


##BAR GRAPHS BASED ON AVERAGES -- WASN'T A GOOD IDEA
    # q1 = st.checkbox('Quartile 1 of Producer GHG Emissions (0-25%)')
    # q2 = st.checkbox('Quartile 2 of Producer GHG Emissions (25-50%)')
    # q3 = st.checkbox('Quartile 3 of Producer GHG Emissions (50-75%)')
    # q3 = st.checkbox('Quartile 4 of Producer GHG Emissions (75-100%)')
    # if q1:
    #     for indicator in indicators:
    #         y_axis = [indicator]
    #         df_filtered[indicator] = df_filtered[indicator].replace(',', '', regex=True).replace('-', '', regex=True).replace('%', '', regex=True).replace(' ', '', regex=True).replace('', 'NaN').astype(float)  # remove commas
    #         df_filtered = format_col(df_filtered, indicator)
    #         average = [df_filtered[indicator].mean()]
    #         fig = px.bar(x=average, y=y_axis,
    #              labels={'x': 'Value'}, template = 'simple_white', orientation='h')
    #         st.plotly_chart(fig)
    

    
