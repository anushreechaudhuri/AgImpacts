import streamlit as st
import pandas as pd

st.set_page_config(layout='wide')
import plotly.express as px

st.title('Welcome to the AgImpacts Interactive Web Tool!')
st.markdown('This is a work in progress. Additional features and polish are on their way!')

@st.cache(show_spinner=False, persist=True)  # save computation between reruns
def get_full_df():
    with st.spinner('Loading excel spreadsheet...'):  # show a progress meter
        full_df = pd.read_excel('AgImpacts_Raw_Data.xlsx', sheet_name=1,
                                header=1)
    return full_df

def format_col(df, col):
    del_things = (',', '-', '%', ' ')
    for del_thing in del_things:
        df[col] = df[col].replace(del_thing, '', regex=True)
    df[col] = df[col].replace('', 'NaN').replace('', 'nan').astype(float, errors='ignore')
    return df[col].dropna()

def format_fig(fig):
    fig.update_layout(
        font_family="IBM Plex Sans",
        font_color="black",
        title_font_family="IBM Plex Sans",
        title_font_color="black",
        legend_title_font_color="black")
    fig.update_xaxes(title_font_family="IBM Plex Sans")
    fig.update_yaxes(title_font_family="IBM Plex Sans")
    return fig

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

numerical_cols = ['GHG Emissions', 'Land Use', 'Eutrophication Potential', 
                'Acidification Potential', 'Freshwater Withdrawal']

col_labels = [  # Tuples of (column name, pretty print name for axis labels)
    ('Land Use','Land Use (m<sup>2</sup>*yr)'),
    ('Eutrophication Potential', 'Eutrophication Potential (kg PO<sub>4</sub><sup>3-</sup> eq)'),
    ('Acidification Potential', 'Acidification Potential (kg SO<sub>2</sub> eq)'),
    ('Freshwater Withdrawal', 'Freshwater Withdrawal (L)')
    ]
col_labels_dict = {'GHG Emissions': 'GHG Emissions (kg CO<sub>2</sub> eq)',
    'Land Use': 'Land Use (m<sup>2</sup>*yr)',
    'Eutrophication Potential': 'Eutrophication Potential (kg PO<sub>4</sub><sup>3-</sup> eq)',
    'Acidification Potential': 'Acidification Potential (kg SO<sub>2</sub> eq)',
    'Freshwater Withdrawal': 'Freshwater Withdrawal (L)'}

indicators = ['Land Use', 'Eutrophication Potential', 
    'Acidification Potential', 'Freshwater Withdrawal']

ghg = 'GHG Emissions'

with st.beta_expander('Indicator Charts'):
    options = st.selectbox(
        'Select Chart Features',
        ['Linear Trendline', 'Non-Linear Trendline',# 'Display Statistics', 'Label by Country', 'Label by System Type'
        ])
    trendline_dict = {
        'Linear Trendline': 'ols',
        'Non-Linear Trendline': 'lowess',
        'Display Statistics' : None,
        'Label by Country' : None, 
        'Label by System Type' : None
        }
    for y, name in col_labels:
        column = format_col(df_filtered, y)
        df_filtered[y] = column
        fig = px.scatter(x=df_filtered['GHG Emissions'],
                    template='simple_white',
            y=df_filtered[y], color=df_filtered['Country'] if options == 'Label by Country' else None, 
            symbol = df_filtered['System'] if options == 'Label by System Type' else None,
            title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
            labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'Country', 'symbol' : 'System'}
            , trendline = trendline_dict[options],
            )
        fig = format_fig(fig)
        st.plotly_chart(fig)
        if options == 'Display Statistics':
            results = px.get_trendline_results(fig)
            st.write(str(results))

with st.beta_expander('Impact Analysis'):
    ghg_col = format_col(df_filtered, ghg)
    df_filtered[ghg] = ghg_col
    ghg_points = sorted(set(ghg_col))
    min_cutoff, max_cutoff = st.select_slider('Select a range of GHG emissions', ghg_points, value=(min(ghg_points), max(ghg_points)))
    st.markdown(f'Your selected range is from {min_cutoff} (kg CO<sub>2</sub> eq) to {max_cutoff} (kg CO<sub>2</sub> eq).', unsafe_allow_html=True)
    cutoff_df = df_filtered.loc[(df_filtered[ghg] <= max_cutoff) & (df_filtered[ghg] >= min_cutoff), ['GHG Emissions', 'Land Use', 'Eutrophication Potential', 
    'Acidification Potential', 'Freshwater Withdrawal']]
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
        fig = px.scatter(x=cutoff_df['GHG Emissions'],
                    template='simple_white',
            y=cutoff_df[y],
            title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
            labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'System'}#, trendline = 'ols'
            )
        fig = format_fig(fig)
        st.plotly_chart(fig)
        st.markdown(f'The median {name} for your selected range is {cutoff_df[y].median()}, and the average is {round(cutoff_df[y].mean(), 5)}.', unsafe_allow_html=True)

with st.beta_expander('Geographic Overview of Indicators'):
    st.markdown('This tool analyzes indicators by geographic region.')
    col = st.selectbox(label='Indicator to Analyze', options=numerical_cols)
    df_filtered[col] = format_col(df_filtered, col)
    data = df_filtered.groupby('Country')[col].mean()
    
    fig = px.scatter_geo(size=data.fillna(0), locations=data.index, locationmode='country names',
                         title=f'Global {col_labels_dict[col]} for {commodity}', labels={'locations': 'Country', 'size': col}, 
                        #  width=1500, height=600
                        template='simple_white')
    fig = format_fig(fig)
    st.plotly_chart(fig)
    fig = px.bar(x=data.index, y=data.fillna(0), title=f'{col_labels_dict[col]} vs. Country for {commodity}',
                 labels={'x': 'Country', 'y': col_labels_dict[col]}, 
                #  width=1500, height=600, 
                template='simple_white')
    fig = format_fig(fig)
    st.plotly_chart(fig)

with st.beta_expander('See Raw Data for Commodity'):
    st.markdown('[See the original data sources here.](https://github.com/anushreechaudhuri/agimpacts/blob/master/AgImpacts_Data_Sources.md)', unsafe_allow_html=True)
    st.dataframe(df_filtered)


##OLD CODE FOR BAR GRAPHS BASED ON AVERAGES -- WASN'T A GOOD IDEA
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
    

    
