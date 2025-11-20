# fixes_streamlit_app.py
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

# optional: enable theme only if available
try:
    alt.themes.enable("dark")
except Exception:
    pass

# Load data
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')

# Ensure population is numeric
df_reshaped['population'] = pd.to_numeric(df_reshaped['population'], errors='coerce').fillna(0).astype(int)

# Sidebar
with st.sidebar:
    st.title('🏂 US Population Dashboard')
    year_list = sorted(df_reshaped.year.unique(), reverse=True)
    selected_year = st.selectbox('Select a year', year_list)
    df_selected_year = df_reshaped[df_reshaped.year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

# helper functions (unchanged except small safety)
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q', legend=None, scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(width=900).configure_axis(labelFontSize=12, titleFontSize=12)
    return heatmap

def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(
        input_df, locations=input_id, color=input_column, locationmode="USA-states",
        color_continuous_scale=input_color_theme,
        range_color=(0, max(df_selected_year.population) if len(df_selected_year) else 0),
        scope="usa",
        labels={'population':'Population'}
    )
    choropleth.update_layout(template='plotly_dark', plot_bgcolor='rgba(0, 0, 0, 0)',
                             paper_bgcolor='rgba(0, 0, 0, 0)', margin=dict(l=0, r=0, t=0, b=0), height=350)
    return choropleth

def make_donut(input_response, input_text, input_color):
    if input_color == 'blue':
        chart_color = ['#29b5e8', '#155F7A']
    elif input_color == 'green':
        chart_color = ['#27AE60', '#12783D']
    elif input_color == 'orange':
        chart_color = ['#F39C12', '#875A12']
    else:
        chart_color = ['#E74C3C', '#781F16']

    source = pd.DataFrame({"Topic": ['', input_text], "% value": [100-input_response, input_response]})
    source_bg = pd.DataFrame({"Topic": ['', input_text], "% value": [100, 0]})

    plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
        theta="% value",
        color= alt.Color("Topic:N",
                         scale=alt.Scale(domain=[input_text, ''], range=chart_color),
                         legend=None),
    ).properties(width=130, height=130)

    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
        theta="% value",
        color= alt.Color("Topic:N",
                         scale=alt.Scale(domain=[input_text, ''], range=chart_color),
                         legend=None),
    ).properties(width=130, height=130)
    return plot_bg + plot + text

def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

def calculate_population_difference(input_df, input_year):
    selected_year_data = input_df[input_df['year'] == input_year].reset_index(drop=True)
    previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index(drop=True)
    # align by state id to avoid index mismatch
    merged = pd.merge(selected_year_data, previous_year_data[['id','population']], on='id', how='left', suffixes=('','_prev'))
    merged['population_prev'] = merged['population_prev'].fillna(0)
    merged['population_difference'] = merged.population - merged.population_prev
    return merged[['states','id','population','population_difference']].sort_values(by="population_difference", ascending=False)

# --- Dashboard main panel ---
# IMPORTANT FIX: use integer ratios for columns
col = st.columns([3, 9, 4], gap='medium')  # <- integers, not floats

with col[0]:
    st.markdown('#### Gains/Losses')
    df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_year)

    if selected_year > df_reshaped.year.min():
        first_state_name = df_population_difference_sorted.states.iloc[0]
        first_state_population = format_number(int(df_population_difference_sorted.population.iloc[0]))
        first_state_delta = format_number(int(df_population_difference_sorted.population_difference.iloc[0]))
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta = ''
    # Pass numeric delta? streamlit accepts string but numeric is better
    try:
        delta_val = int(df_population_difference_sorted.population_difference.iloc[0])
    except Exception:
        delta_val = None
    st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)

    if selected_year > df_reshaped.year.min():
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(int(df_population_difference_sorted.population.iloc[-1]))   
        last_state_delta = format_number(int(df_population_difference_sorted.population_difference.iloc[-1]))   
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=last_state_population, delta=last_state_delta)

    st.markdown('#### States Migration')
    if selected_year > df_reshaped.year.min():
        df_greater_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference > 50000]
        df_less_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference < -50000]
        states_migration_greater = round((len(df_greater_50000)/df_population_difference_sorted.states.nunique())*100)
        states_migration_less = round((len(df_less_50000)/df_population_difference_sorted.states.nunique())*100)
    else:
        states_migration_greater = 0
        states_migration_less = 0

    donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
    donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')

    migrations_col = st.columns((0.2, 1, 0.2))
    with migrations_col[1]:
        st.write('Inbound')
        st.altair_chart(donut_chart_greater, use_container_width=True)
        st.write('Outbound')
        st.altair_chart(donut_chart_less, use_container_width=True)

with col[1]:
    st.markdown('#### Total Population')
    choropleth = make_choropleth(df_selected_year, 'states_code', 'population', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)
    heatmap = make_heatmap(df_reshaped, 'year', 'states', 'population', selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)

with col[2]:
    st.markdown('#### Top States')
    # IMPORTANT FIX: remove width=None and use use_container_width=True
    st.dataframe(
        df_selected_year_sorted[['states','population']],
        hide_index=True,
        use_container_width=True,
        column_config={
            "states": st.column_config.TextColumn("States"),
            "population": st.column_config.ProgressColumn(
                "Population",
                format="%f",
                min_value=0,
                max_value=int(df_selected_year_sorted.population.max() if len(df_selected_year_sorted) else 0),
            )
        }
    )

    with st.expander('About', expanded=True):
        st.write('''
            - Data: [U.S. Census Bureau](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html).
            - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
            - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
            ''')
