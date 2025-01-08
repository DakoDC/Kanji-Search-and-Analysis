

###################### Plots ##########################
import polars as pl
import streamlit as st
import altair as alt
from pyvis.network import Network

from app import kanjis

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
        alt.Y("jlpt_new:O", sort="descending"),
        alt.X("strokes"),
        alt.Size("character", title="Number of kanjis"),
    )
).properties(
    title="Amount of Kanjis by JLPT Level and Stroke Count",

    height = 200,
    width = 480
)

st.altair_chart(chart)
# The more difficult the level the more strokes are needed

# there seems to be somewhat of a normal distribution among all levels,
# getting clearer with the increase in difficulty (and in amount of kanjis)







###################################################

# most used radicals

# keep only the most used kanjis (for clearer and faster to load results)
kanjis_filtered = (
    kanjis
    .filter(pl.col("freq") < 125)
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
    # @st.cache_data
    def show_network():
        st.components.v1.html(html_content, height=600)
    show_network()

with col2:
    st.markdown(
        """
        <div style="
            border: 2px solid white; 
            border-radius: 10px; 
            padding: auto; 
            background-color: gray; 
            color: white;
            width: 115px;
        ">
            <h4 style="margin-top: 0;">Legend:</h4>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="width: 12px; height: 12px; background-color: navy; border-radius: 50%; margin-right: 8px;"></div>
                <span>Radicals</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 12px; height: 12px; background-color: cyan; border-radius: 50%; margin-right: 8px;"></div>
                <span>Kanjis</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )




