

###################### Plots ##########################
import polars as pl
import streamlit as st
import altair as alt
from pyvis.network import Network

from app import kanjis # import the kanjis df from app.py


# configures the streamlit page layout
st.set_page_config(layout="wide") 





st.write("# Graphical Analysis")
st.write("Here you can see the graphical analysis of all the kanjis")
st.write(" ")



# adds columns with the number of elements in the lists of other columns
kanjis_count = kanjis.with_columns(
    pl.col("meanings").list.len()
    .alias("count_meanings"),
    
    pl.col("readings_on").list.len()
    .alias("count_readings_on"),
    
    pl.col("readings_kun").list.len()
    .alias("count_readings_kun"),
    
    pl.col("wk_radicals").list.len() 
    .alias("count_wk_radicals")
)

# number of kanjis for each jlpt level and number of strokes
jlpt_strokes = (
    kanjis_count
    .group_by(pl.col(["jlpt_new","strokes"]))
    .agg(pl.col("character").count())
    .filter(~pl.col("jlpt_new").is_null())
)

chart = (
    alt.Chart(jlpt_strokes.to_pandas())
    .mark_circle()
    .encode(
        alt.Y("jlpt_new:O", sort="descending", title="JLPT level"),
        alt.X("strokes", title="Number of strokes"),
        alt.Size("character", title="Number of kanjis"),
    )
).properties(
    title="Amount of Kanjis by JLPT Level and Stroke Count",

    height = 300,
    width = 660
)
col1,col2 = st.columns([3,5], gap="large") # creates n_cols spaces where to put each df

with(col1):
    st.write(
        '''
        Analysis:    
          
        Generally, the more difficult is the level, the more strokes are needed for the kanji.  

        There also seems to be mostly a simmetric distribution among all levels ecept the easiest (5),
        getting clearer with the increase in difficulty (and in amount of kanjis)
        ''')
with(col2):
    st.altair_chart(chart)




st.write('''
         ---  
         ---
         ''')


####################
import numpy as np

a = kanjis.select(
    pl.col(["grade","freq"])
    .filter(~pl.col("freq").is_null())
).filter(~pl.col("grade").is_null())

a = a.with_columns(
    grade_jitter = pl.col("grade") + np.random.uniform(-0.2, 0.2, len(a))
)

# a['grade2'] = a['grade'] + np.random.uniform(-0.1, 0.1, len(a))
# a['y_jittered'] = a['y'] + np.random.uniform(-0.1, 0.1, len(a))

chart = (
    alt.Chart(a.to_pandas())
    .mark_circle(opacity=0.5)#(size=20)
    .encode(
        alt.X("grade_jitter:Q", title="School Grade"),
        alt.Y("freq:Q", title="Kanji frequency"),
        )
).properties(
    title="Distribution of the kanjis  by school Grade Level and frequency of daily use",

    height = 600,
    width = 660
)

col1,col2 = st.columns([5,3], gap="large") # creates n_cols spaces where to put each df
with(col1):
    st.altair_chart(chart)
with(col2):
    st.write(
        '''
        Analysis:    
          
        The distribution shows that the more a kanjis is frequent in daily life, the more it is learned early in school.  
        There also seems to be an uppword trend, where the least used kanjis are also the latest learned.
        
        The gap in the 7th year is probably to be explained by the dataframe used for the data,
        which most likely grouped the 7th and 8th grade kanjis together
        ''')

st.write('''
         ---  
         ---
         ''')

###################################################

# most used radicals

st.write("### Graph of kanjis and radicals")
st.write("The graph shows the connections between the most used 125 kanjis and their respective radicals")
st.write("(You can move or increase/decrease the field of view at will)")


# keep only the most used kanjis (for clearer and faster to load results)
kanjis_filtered = (
    kanjis
    .filter(pl.col("freq") < 1) # recommended 125 kanjis for a good balance of quantity and readability 
    .select(pl.col(["character", "wk_radicals"]))
)

# Total amount of times each radical appears in the kanjis_filtered df 
radicals_count = (
    kanjis_filtered
    .explode("wk_radicals")
    .select(pl.col("wk_radicals").value_counts(sort=True))
    .unnest("wk_radicals")
)

# normalize the count column, to have consistent proportions for the plot
radicals_count_norm = (
    radicals_count
    .with_columns(
        count = pl.col("count") / pl.col("count").max()
        )
    )

# create a dict from the df
radicals_count_dict = dict(zip(radicals_count['wk_radicals'], radicals_count_norm['count']))


# initialize PyVis Network
net = Network(bgcolor="gray", font_color="white")


# add nodes for kanji and radicals
for kanji, radicals in kanjis_filtered.iter_rows():

    # add kanji node
    net.add_node(kanji, label=kanji, color='cyan', size=10)
    
    # add radical nodes and edges
    for radical in radicals:

        # add radical node
        net.add_node(radical, label=radical, color='navy', size=radicals_count_dict[radical]*30)
        # add edge between kanji and radical
        net.add_edge(kanji, radical)

# save the network as an HTML file
output_path = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\simple_network.html"

net.save_graph(output_path)

# read the html file
with open(output_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# show the plot in Streamlit



col1, col2 = st.columns([10, 1])  # Make the plot wider than the legend
with col1:
    def show_network():
        st.components.v1.html(html_content, height=600)
    show_network()

with col2:
    st.markdown(
        """
        <div style="
            border: 1px solid white; 
            border-radius: 10px; 
            padding: auto; 
            background-color: gray; 
            color: white;
            width: 115px;
        ">
            <h4 style="margin-top: 0;">Legend:</h4>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 12px; height: 12px; background-color: navy; border-radius: 50%; margin-right: 5px"></div>
                <span>Radicals</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 12px; height: 12px; background-color: cyan; border-radius: 50%; margin-right: 5px;"></div>
                <span>Kanjis</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )




