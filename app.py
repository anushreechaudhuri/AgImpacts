import streamlit as st
import pandas as pd
import plotly.express as px
from bokeh.models.widgets import Div
st.set_page_config(layout='wide')


st.title('Welcome to the AgImpacts Interactive Web Tool!')
st.markdown('This interactive web tool is a part of AgImpacts, a project conducted by ten MIT undergraduates for the World Wilfelife Fund. AgImpacts analyzes environmental trade-offs for ten agricultural commodities across five indicators: GHG emissions, land use, eutrophication potential, acidification potential, and freshwater withdrawal. To learn more about these topics and our project, [visit the AgImpacts website.](https://agimpacts.wpengine.com/)', unsafe_allow_html=True)
st.markdown('Select a commodity of interest on the left sidebar to start. For a comprehensive guide to using this web tool, click on the **Tool Usage Guide** section below.')
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
commodity_rows['Tuna'] = (507, 600) #596, 586
# Select the commodity to analyze
commodity = st.sidebar.selectbox(label='Select a Commodity', options=list(commodity_rows.keys()))
start, end = commodity_rows[commodity]
df_filtered = full_df[start:end].dropna(axis=0, subset=['Reference'])
numerical_cols = ['GHG Emissions', 'Land Use', 'Eutrophication Potential', 
                'Acidification Potential', 'Freshwater Withdrawal']

col_labels = [  # Tuples of (column name, pretty print name for axis labels)
    ('Land Use','Land Use (m<sup>2</sup>*yr)'),
    ('Eutrophication Potential', 'Eutrophication Potential (kg PO<sub>4</sub><sup>3-</sup> eq.)'),
    ('Acidification Potential', 'Acidification Potential (kg SO<sub>2</sub> eq.)'),
    ('Freshwater Withdrawal', 'Freshwater Withdrawal (L)')
    ]
col_labels_dict = {'GHG Emissions': 'GHG Emissions (kg CO<sub>2</sub> eq.)',
    'Land Use': 'Land Use (m<sup>2</sup>*yr)',
    'Eutrophication Potential': 'Eutrophication Potential (kg PO<sub>4</sub><sup>3-</sup> eq.)',
    'Acidification Potential': 'Acidification Potential (kg SO<sub>2</sub> eq.)',
    'Freshwater Withdrawal': 'Freshwater Withdrawal (L)'}

indicators = ['Land Use', 'Eutrophication Potential', 
    'Acidification Potential', 'Freshwater Withdrawal']
web_links = {'Maize' : 'https://agimpacts.wpengine.com/maize/',
    'Palm Oil' : 'https://agimpacts.wpengine.com/palm-oil/',
    'Soybeans' : 'https://agimpacts.wpengine.com/soybeans/',
    'Coffee' : 'https://agimpacts.wpengine.com/coffee/',
    'Roundwood' : 'https://agimpacts.wpengine.com/roundwood/',
    'Beef' : 'https://agimpacts.wpengine.com/beef/',
    'Poultry Meat' : 'https://agimpacts.wpengine.com/poultry-meat/',
    'Salmon' : 'https://agimpacts.wpengine.com/salmon/',
    'Shrimp' : 'https://agimpacts.wpengine.com/shrimp/',
    'Tuna' : 'https://agimpacts.wpengine.com/tuna/'
    }
ghg = 'GHG Emissions'

with st.beta_expander('Impact Analysis'):
    trendline_dict = {
        'Linear Trendline': 'ols',
        'Non-Linear Trendline': 'lowess',
        'None' : None
        }
    ghg_col = format_col(df_filtered, ghg)
    df_filtered[ghg] = ghg_col
    ghg_points = sorted(set(ghg_col))
    min_cutoff, max_cutoff = st.select_slider('Select a range of GHG emissions', ghg_points, value=(min(ghg_points), max(ghg_points)))
    st.markdown(f'Your selected range is from {min_cutoff} (kg CO<sub>2</sub> eq) to {max_cutoff} (kg CO<sub>2</sub> eq).', unsafe_allow_html=True)
    cutoff_df = df_filtered.loc[(df_filtered[ghg] <= max_cutoff) & (df_filtered[ghg] >= min_cutoff) & (df_filtered[ghg] >= 0.0), ['GHG Emissions', 'Land Use', 'Eutrophication Potential', 
    'Acidification Potential', 'Freshwater Withdrawal', 'Country', 'System']] # for some reason >= 0 isn't working
    show_data = st.checkbox('Show Filtered Raw Data')
    if show_data:
        st.dataframe(cutoff_df)
    show_quantiles = st.checkbox('Show Quantiles of GHG Emissions')
    if show_quantiles:
            quantile_list = df_filtered[ghg].quantile([0.25,0.5,0.75, 1.0])
            quantile_list = pd.DataFrame(quantile_list)
            st.dataframe(quantile_list)
    options = st.selectbox(
        'Select Trendline',
        ['Linear Trendline', 'Non-Linear Trendline', 'None'], index=2)
    features = st.multiselect('Select Additional Features', ['Label by Country', 'Label by System Type', 'Display Median and Average', 'Display Advanced Statistics'
    ])
    for y, name in col_labels:
        df_filtered[y] = format_col(df_filtered, y)
        cutoff_df[y] = format_col(cutoff_df, y)
        if 'Label by Country' in features:
            cutoff_df = format_df_col(cutoff_df, 'Country')
        if 'Label by System Type' in features:
            cutoff_df = format_df_col(cutoff_df, 'System')
        empty_graph = cutoff_df[y].isnull().values.all() or cutoff_df[ghg].isnull().values.all()
        if empty_graph:
            st.markdown(f'A graph for {name} cannot be generated because there is no data for this indicator.', unsafe_allow_html = True)
        elif not empty_graph:
            fig = px.scatter(x=cutoff_df['GHG Emissions'],
                        template='simple_white',
                y=cutoff_df[y]
                , color= cutoff_df['Country'] if 'Label by Country' in features else None
                , symbol = cutoff_df['System'] if 'Label by System Type' in features else None
                , title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
                labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'Country', 'symbol' : 'System'}
                , trendline = trendline_dict[options]
                )
            fig = format_fig(fig)
            st.plotly_chart(fig)
            if 'Display Median and Average' in features:
                try:
                    st.markdown(f'The median {name} for your selected range is {round(cutoff_df[y].median(), 5)}, compared to {round(df_filtered[y].median(skipna=True), 5)} for the full range, and the average is {round(cutoff_df[y].mean(), 5)}, compared to {round(df_filtered[y].mean(skipna=True), 5)} for the full range.', unsafe_allow_html=True)
                except:
                    st.markdown(f'The median {name} for your selected range is {round(cutoff_df[y].median(), 5)}, and the average is {round(cutoff_df[y].mean(), 5)}.', unsafe_allow_html=True)
                    st.markdown('Due to an error, the compared median and average cannot be displayed for this chart.')
            if 'Display Advanced Statistics' in features and (options == 'Linear Trendline') and empty_graph == False and cutoff_df[y].describe().loc['count']>5:
                try:
                    results = px.get_trendline_results(fig)
                    results_table = results.px_fit_results.iloc[0].summary().tables[1]
                    st.markdown(f'### Statistical Values for {name} vs. GHG Emissions (kg CO<sub>2</sub> eq)', unsafe_allow_html=True)
                    st.dataframe(results_table)
                except:
                    pass
            elif 'Display Advanced Statistics' in features and empty_graph == False and cutoff_df[y].describe().loc['count']>5:
                st.markdown('Select a linear trendline to display advanced statistics.')
            elif 'Display Advanced Statistics' in features:
                st.markdown('There is not enough data to display advanced statistics.')

with st.beta_expander('Geographic Analysis'):
    st.markdown('This tool analyzes indicators by geographic region.')
    col = st.selectbox(label='Indicator to Analyze', options=numerical_cols)
    df_filtered[col] = format_col(df_filtered, col)
    # df_filtered = df_filtered.sort_values(by=col, ascending=False)
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
        data.sort_values(ascending=False, inplace=True)  # this sorts countries from greatest to least instead of alphabetically!
        fig = px.bar(x=data.index, y=data.fillna(0), title=f'{col_labels_dict[col]} vs. Country for {commodity}',
                    labels={'x': 'Country', 'y': col_labels_dict[col]}, 
                    #  width=1500, height=600, 
                    template='simple_white')
        fig = format_fig(fig)
        st.plotly_chart(fig)
commodity_raw_data = f'Raw Data for {commodity}'
with st.beta_expander(commodity_raw_data):
    st.markdown('[See the original data sources here.](https://github.com/anushreechaudhuri/agimpacts/blob/master/AgImpacts_Data_Sources.md)', unsafe_allow_html=True)
    st.dataframe(df_filtered)
with st.beta_expander('Tool Usage Guide'):
    st.markdown('This is a tool for exploratory analysis. First, select a commodity in the left sidebar. Next, click on a section of interest. The purpose of each section is described below:')
    st.markdown('* **Impact Analysis** displays scatter plots of each environmental indicator vs. GHG emissions, with features allowing for selection of a range of GHG emissions, a linear and non-linear trendline, labeling by country and/or system, and displaying the median, average, and advanced statistics for each chart.')
    st.markdown('* **Geographic Analysis** first displays a map plot of a selected indicator by country, with the size of each circle reflecting the average magnitude of the indicator in that country. Next, it displays a bar graph showing the average indicator value by country, ordered from highest to lowest magnitude to easily identify countries with high average environmental impact from a selected indicator.')
    st.markdown(f'* **Raw Data for {commodity}** displays an interactive table of raw data for the selected commodity and a link to view and download our original data soures. To read more about the selected commodity, including interpretation and takeaways from the data, click the link below this section.', unsafe_allow_html=True)
    st.text('')
    st.markdown('All charts in this web tool are interactive. Useful features include zooming in and out, filtering by label to isolate a country or system of interest, hovering to see details on each data point and trendline, and downloading any plot as a png. Tables are also interactive; each column can be filtered and sorted. For a more in-depth tutorial on using this tool, including a walk-through of the interactive chart features, watch the screencast linked below.')
    st.markdown('#### [Watch a Screencast on Using This Tool](https://agimpacts.wpengine.com/)', unsafe_allow_html=True)
    st.text('')
    st.markdown('To report a bug, share this tool, view the source code, or record a screencast of your own usage of this tool to share with others, click the horizontal menu bars. For queries about this web tool, contact Anushree Chaudhuri (anuc@mit.edu) or Emily Moberg (emily.a.moberg@gmail.com).', unsafe_allow_html=True)
st.text('')
link = web_links[commodity]
st.markdown(f'#### [Read More About {commodity} on the AgImpacts Website]({link})', unsafe_allow_html=True)
st.text('')
st.markdown('<sup>Note: all functional units for indicators are "kg unit eq. *per kg product*."</sup>', unsafe_allow_html=True)
# HACKY BUTTON WINDOW JS CODE
    # commodity_button = f'Read More About {commodity} on the AgImpacts Website'
    # if st.button(commodity_button):
    #     link = f"window.open('{web_links[commodity]}')"
    #     #js = "window.open('https://www.streamlit.io/')"  # New tab or window
    #     js = link
    #     html = '<img src onerror="{}">'.format(js)
    #     div = Div(text=html)
    #     st.bokeh_chart(div)    

# OLD IMPACT ANALYSIS CODE 
    # with st.beta_expander('Impact Analysis'):
    #     options = st.selectbox(
    #         'Select Trendline',
    #         ['Linear Trendline', 'Non-Linear Trendline', 'None'], index=2)
    #     trendline_dict = {
    #         'Linear Trendline': 'ols',
    #         'Non-Linear Trendline': 'lowess',
    #         'None' : None
    #         }
    #     features = st.multiselect('Select Additional Features', ['Label by Country', 'Label by System Type', 'Display Statistics'
    #     ])
    #     ghg_col = format_col(df_filtered, ghg)
    #     df_filtered[ghg] = ghg_col
    #     ghg_points = sorted(set(ghg_col))
    #     min_cutoff, max_cutoff = st.select_slider('Select a range of GHG emissions', ghg_points, value=(min(ghg_points), max(ghg_points)))
    #     st.markdown(f'Your selected range is from {min_cutoff} (kg CO<sub>2</sub> eq) to {max_cutoff} (kg CO<sub>2</sub> eq).', unsafe_allow_html=True)
    #     cutoff_df = df_filtered.loc[(df_filtered[ghg] <= max_cutoff) & (df_filtered[ghg] >= min_cutoff), ['GHG Emissions', 'Land Use', 'Eutrophication Potential', 
    #     'Acidification Potential', 'Freshwater Withdrawal']]
    #     show_data = st.checkbox('Show Filtered Raw Data')
    #     show_quantiles = st.checkbox('Show Quantiles of GHG Emissions')
    #     if show_data:
    #         st.dataframe(cutoff_df)
    #     if show_quantiles:
    #             quantile_list = df_filtered[ghg].quantile([0.25,0.5,0.75, 1.0])
    #             quantile_list = pd.DataFrame(quantile_list)
    #             st.dataframe(quantile_list)
    #     for y, name in col_labels:
    #         cutoff_df[y] = format_col(cutoff_df, y)
    #         empty_graph = df_filtered[y].isnull().values.all() or df_filtered[ghg].isnull().values.all()
    #         if empty_graph:
    #             st.markdown(f'A graph for {name} cannot be generated because there is no data for this indicator.', unsafe_allow_html = True)
    #         elif not empty_graph:
    #             fig = px.scatter(x=cutoff_df['GHG Emissions'],
    #                         template='simple_white',
    #                 y=cutoff_df[y],
    #                 title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
    #                 labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'System'}#, trendline = 'ols'
    #                 )
    #             fig = format_fig(fig)
    #             st.plotly_chart(fig)
    #             st.markdown(f'The median {name} for your selected range is {cutoff_df[y].median()}, and the average is {round(cutoff_df[y].mean(), 5)}.', unsafe_allow_html=True)

# OLD INDICATOR CHARTS CODE (COMBINED IN NEW IMPACT ANALYSIS SECTION)
    # with st.beta_expander('Indicator Charts'):
    # options = st.selectbox(
    #     'Select Trendline',
    #     ['Linear Trendline', 'Non-Linear Trendline', 'None'], index=2)
    # trendline_dict = {
    #     'Linear Trendline': 'ols',
    #     'Non-Linear Trendline': 'lowess',
    #     'None' : None
    #     }
    # features = st.multiselect('Select Additional Features', ['Label by Country', 'Label by System Type', 'Display Statistics'
    # ])
    # for y, name in col_labels:
    #     df_plot = format_df_col(df_filtered, y)
    #     if 'Label by Country' in features:
    #         df_plot = format_df_col(df_plot, 'Country')
    #     if 'Label by System Type' in features:
    #         df_plot = format_df_col(df_plot, 'System')
    #     empty_graph = df_plot[y].isnull().values.all() or df_plot[ghg].isnull().values.all()
    #     if empty_graph:
    #         st.markdown(f'A graph for {name} cannot be generated because there is no data for this indicator.', unsafe_allow_html = True)
    #     elif not empty_graph:
    #         fig = px.scatter(x=df_plot['GHG Emissions'],
    #                     template='simple_white',
    #             y=df_plot[y]
    #             , color= df_plot['Country'] if 'Label by Country' in features else None
    #             , symbol = df_plot['System'] if 'Label by System Type' in features else None
    #             , title=f'{name} vs. GHG Emissions (kg CO<sub>2</sub> eq)',
    #             labels={'x': 'GHG Emissions (kg CO<sub>2</sub> eq)', 'y':name, 'color' : 'Country', 'symbol' : 'System'}
    #             , trendline = trendline_dict[options]
    #             )
    #         fig = format_fig(fig)
    #         st.plotly_chart(fig)
    #         if 'Display Statistics' in features and (options == 'Linear Trendline' or options == 'Non-Linear Trendline') and empty_graph == False and df_plot[y].describe().loc['count']>5:
    #             try:
    #                 results = px.get_trendline_results(fig)
    #                 results_table = results.px_fit_results.iloc[0].summary().tables[1]
    #                 st.markdown(f'### Statistical Values for {name} vs. GHG Emissions (kg CO<sub>2</sub> eq)', unsafe_allow_html=True)
    #                 st.dataframe(results_table)
    #             except:
    #                 pass
    #         elif 'Display Statistics' in features and empty_graph == False and df_plot[y].describe().loc['count']>5:
    #             st.markdown('Select a trendline to display statistics.')
    #         elif 'Display Statistics' in features:
    #             st.markdown('There is not enough data to display statistics.')

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
    

    
