import streamlit as st
import pandas as pd
import plotly.express as px
from bokeh.models.widgets import Div
st.set_page_config(layout='wide')


st.title('Welcome to the AgImpacts Interactive Web Tool!')
st.markdown('This is a work in progress. Additional features and polish are on their way!')

@st.cache(show_spinner=False, persist=True)  # save computation between reruns
def get_full_df():
    with st.spinner('Loading excel spreadsheet...'):  # show a progress meter
        full_df = pd.read_excel('AgImpacts_Raw_Data.xlsx', sheet_name=1,
                                header=1)
    return full_df

def format_col(df, col):
    del_things = (',', '-', '%', ' ', '  ')
    for del_thing in del_things:
        df[col] = df[col].replace(del_thing, '', regex=True)
    df[col] = df[col].replace('', 'NaN').replace('', 'nan').astype(float, errors='ignore')
    return df[col].dropna()

def format_df_col(df, col):
    col_values = format_col(df, col)
    df[col] = col_values
    df = df[df[col].notna()]
    return df

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
commodity_rows['Tuna'] = (596, 686)
# Select the commodity to analyze
commodity = st.sidebar.selectbox(label='Select a Commodity', options=list(commodity_rows.keys()))
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
web_links = {'Maize (Meal)' : 'https://agimpacts.wpengine.com/',
    'Palm Oil' : 'https://agimpacts.wpengine.com/',
    'Soybean' : 'https://agimpacts.wpengine.com/',
    'Coffee' : 'https://agimpacts.wpengine.com/',
    'Roundwood' : 'https://agimpacts.wpengine.com/',
    'Beef' : 'https://agimpacts.wpengine.com/',
    'Poultry' : 'https://agimpacts.wpengine.com/',
    'Salmon' : 'https://agimpacts.wpengine.com/',
    'Shrimp' : 'https://agimpacts.wpengine.com/',
    'Tuna' : 'https://agimpacts.wpengine.com/'
    }
ghg = 'GHG Emissions'

with st.beta_expander('Indicator Charts'):
    options = st.selectbox(
        'Select Trendline',
        ['Linear Trendline', 'Non-Linear Trendline', 'None'], index=2)
    trendline_dict = {
        'Linear Trendline': 'ols',
        'Non-Linear Trendline': 'lowess',
        'None' : None
        }
    features = st.multiselect('Select Additional Features', ['Label by Country', 'Label by System Type', 'Display Statistics'
    ])
    for y, name in col_labels:
        df_plot = format_df_col(df_filtered, y)
        if 'Label by Country' in features:
            df_plot = format_df_col(df_plot, 'Country')
        if 'Label by System Type' in features:
            df_plot = format_df_col(df_plot, 'System')
        empty_graph = df_plot[y].isnull().values.all() or df_plot[ghg].isnull().values.all()
        if empty_graph:
            st.markdown(f'A graph for {name} cannot be generated because there is no data for this indicator.', unsafe_allow_html = True)
        elif not empty_graph:
            fig = px.scatter(x=df_plot['GHG Emissions'],
                        template='simple_white',
                y=df_plot[y]
                , color= df_plot['Country'] if 'Label by Country' in features else None
                , symbol = df_plot['System'] if 'Label by System Type' in features else None
                , title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
                labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'Country', 'symbol' : 'System'}
                , trendline = trendline_dict[options]
                )
            fig = format_fig(fig)
            st.plotly_chart(fig)
            if 'Display Statistics' in features and (options == 'Linear Trendline' or options == 'Non-Linear Trendline') and empty_graph == False and df_plot[y].describe().loc['count']>5:
                try:
                    results = px.get_trendline_results(fig)
                    results_table = results.px_fit_results.iloc[0].summary().tables[1]
                    st.markdown(f'### Statistical Values for {name} vs. GHG Emissions (kg CO<sub>2</sub> eq)', unsafe_allow_html=True)
                    st.dataframe(results_table)
                except:
                    pass
            elif 'Display Statistics' in features and empty_graph == False and df_plot[y].describe().loc['count']>5:
                st.markdown('Select a trendline to display statistics.')
            elif 'Display Statistics' in features:
                st.markdown('There is not enough data to display statistics.')

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
        empty_graph = df_filtered[y].isnull().values.all() or df_filtered[ghg].isnull().values.all()
        if empty_graph:
            st.markdown(f'A graph for {name} cannot be generated because there is no data for this indicator.', unsafe_allow_html = True)
        elif not empty_graph:
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
    empty_graph = df_filtered[col].isnull().values.all() 
    if empty_graph:
        st.markdown(f'Graphs for {col} cannot be generated because there is no data for this indicator.', unsafe_allow_html = True)
    elif not empty_graph:
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
commodity_raw_data = f'See Raw Data for {commodity}'
with st.beta_expander(commodity_raw_data):
    st.markdown('[See the original data sources here.](https://github.com/anushreechaudhuri/agimpacts/blob/master/AgImpacts_Data_Sources.md)', unsafe_allow_html=True)
    st.dataframe(df_filtered)
st.text('')
commodity_button = f'Read More About {commodity} on the AgImpacts Website'
if st.button(commodity_button):
    link = f"window.open('{web_links[commodity]}')"
    #js = "window.open('https://www.streamlit.io/')"  # New tab or window
    js = link
    html = '<img src onerror="{}">'.format(js)
    div = Div(text=html)
    st.bokeh_chart(div)

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
    

    
