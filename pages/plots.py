

###################### Plots ##########################
import polars as pl
import streamlit as st
import altair as alt
import random # create jitter for a plot

from pyvis.network import Network # graph of the kanjis and radicals

from app import kanjis, kanjis_only # import the dataframes from app.py


# configures the streamlit page layout
st.set_page_config(layout="wide") 


st.write("# Graphical Analysis")
st.write("Here you can see a graphical analysis of all the kanjis")

# spacing between charts
st.write(
    '''
    ---  
    ---
    ''')




########## Amount of kanjis per JLPT level ##############

# It's used the kanjis_only df beacuase the kanjis df also contains the phrases 
jlpt_barplot = kanjis_only.select(pl.col("jlpt_new")).filter(~pl.col("jlpt_new").is_null())

bars = (
    alt.Chart(jlpt_barplot.to_pandas())
    .mark_bar(stroke="gray")
    .encode(
        alt.Y("jlpt_new:O", sort="descending", title="JLPT level"),
        alt.X("count():Q", title="Number of kanjis"),
        alt.Color(
            "jlpt_new:Q",
            scale=alt.Scale(domain=[5, 1], range=['#9932CC', 'navy']),
            legend=None
        )
    )
)



text = alt.Chart(jlpt_barplot.to_pandas()).mark_text(
    align='center',
    baseline='bottom',
    dy=4,  # Adjust position above bars,
    dx=-15,
    color="white"
).encode(
    alt.Y('jlpt_new:O', sort="descending"),
    alt.X('count():Q'),
    alt.Text('count():Q')  # Display the count value
)

chart = bars + text

chart = chart.properties(
    title="Amount of Kanjis per JLPT Level",

    height = 300,
    width = 600
)

col1,col2 = st.columns([5,3], gap="large") # creates n_cols spaces where to put each df


with(col1):
    st.altair_chart(chart)
with(col2):
    st.write("###### Analysis:")
    st.write(
        '''
        The amount of kanjis seems exponential with the difficult,
        by doubling each time, for the excepetion of the Level 2,
        which has the same quantity as Level 3.  

        It's also interesting to notice that the most difficult level (1),
        requires more kanjis to be learned than all the others summed together:
        - levels 5-2 = 979  
        - level 1 = 1232  
        ''')


st.write(
    '''
    ---  
    ---
    ''')



#########################

# number of kanjis for each jlpt level and number of strokes
jlpt_strokes = (
    kanjis
    .group_by(pl.col(["jlpt_new","strokes"]))
    .agg(pl.col("character").count())
    .filter(~pl.col("jlpt_new").is_null())
)

chart = (
    alt.Chart(jlpt_strokes.to_pandas())
    .mark_circle(color='BlueViolet')
    .encode(
        alt.Y("jlpt_new:O", sort="descending", title="JLPT level"),
        alt.X("strokes", title="Number of strokes"),
        alt.Size("character", title="Number of kanjis", legend=alt.Legend(type="symbol"))

    )
).properties(
    title="Amount of Kanjis by JLPT Level and Stroke Count",
    height = 300,
    width = 660
)
col1,col2 = st.columns([3,5], gap="large") # creates n_cols spaces where to put each df

with(col1):
    st.write("###### Analysis:")
    st.write(
        '''
        Generally, the more difficult is the level, the more strokes are needed for the kanji.  

        There also seems to be mostly a simmetric distribution among all levels ecept the easiest (5),
        getting clearer with the increase in difficulty (and in amount of kanjis).
        ''')
with(col2):
    st.altair_chart(chart)




st.write(
    '''
    ---  
    ---
    ''')





####### Distribution of the kanjis by school Grade Level and frequency of daily use #########

# df for the jitter plot
kanjis_jitter = (
    kanjis
    .select(pl.col(["grade","freq"]))
    .filter(~(pl.col("grade").is_null() | pl.col("freq").is_null()))
)

kanjis_jitter = (
    kanjis_jitter
    .with_columns( # add jitter to the x (grade) 
        grade_jitter = pl.col("grade") + pl.Series([random.uniform(-0.2, 0.2) for _ in range(len(kanjis_jitter))])
    )
)

chart = (
    alt.Chart(kanjis_jitter.to_pandas())
    .mark_circle(opacity=0.5, color='BlueViolet')
    .encode(
        alt.X("grade_jitter:Q", title="School Grade"),
        alt.Y("freq:Q", title="Kanji frequency"),
        )
).properties(
    title="Distribution of the kanjis by school Grade Level and frequency of daily use",
    height = 600,
    width = 660
)


col1,col2 = st.columns([5,3], gap="large") # creates n_cols spaces where to put each df

with(col1):
    st.altair_chart(chart)

with(col2):
    st.write("###### Analysis:")
    st.write(
        '''  
        The distribution shows that the more a kanjis is frequent in daily life, the more it is learned early in school.  
        There also seems to be an uppword trend, where the least used kanjis are also the latest learned.
        
        The gap in the 7th year is probably to be explained by the dataframe used for the data,
        which most likely grouped the 7th and 8th grade kanjis together.
        ''')

st.write(
    '''
    ---  
    ---
    ''')




###### Distribution of Kanjis by Daily Frequency use and Stroke Count ######
kanjis_only_notNull = (
    kanjis_only
    .select(pl.col(["strokes","freq", "jlpt_new"]))

    .filter(~(pl.col("strokes").is_null() | pl.col("freq").is_null() | pl.col("jlpt_new").is_null()))
)

chart = (
    alt.Chart(kanjis_only_notNull.to_pandas())
    .mark_circle(opacity=0.7)
    .encode(
        alt.X("strokes:Q", title="Number of strokes"),
        alt.Y("freq:Q", title="Kanji frequency"),
        alt.Color("jlpt_new:Q",title="JLPT level",scale=alt.Scale(domain=[5,1], range = ['fuchsia', 'Blue']), legend=alt.Legend(type="symbol")))
).properties(
    title="Distribution of Kanjis by Daily Frequency use and Stroke Count",
    height = 600,
    width = 660
)
col1,col2 = st.columns([3,5], gap="large") # creates n_cols spaces where to put each df

with(col1):
    st.write("###### Analysis:")
    st.write(
        '''
        For the exception of the first ~200 most used kanjis,
        it seems like the distribution among the number of strokes per kanji tends to stay similar with the decrease in usage of the kanjis.  
        
        Also as expected the most frequent kanjis tend to have less strokes and an inferior JLPT level.  

        Some of the most interesting outliers are:
        - 乙, "The latter (item)", which has 1 stroke but JLPT level 1.
        - 議, "deliberation", with 20 strokes and JLPT level 3.
        - 題, "topic" with 18 strokes and JLPT level 4.
        ''')
with(col2):
    st.altair_chart(chart)

st.write(
    '''
    ---  
    ---
    ''')


###########################
# adds columns with the number of elements in the lists of other columns
kanjis_count = kanjis_only.select(
    pl.col("meanings").list.len()
    .alias("count_meanings"),
    
    pl.col("readings_on").list.len()
    .alias("count_readings_on"),
    
    pl.col("readings_kun").list.len()
    .alias("count_readings_kun"),
    
    pl.col("wk_radicals").list.len() 
    .alias("count_wk_radicals")
)

kanjis_count = kanjis_count.group_by(pl.col(["count_readings_on","count_readings_kun"])).agg(pl.count())
kanjis_count = kanjis_count.with_columns(
    count_log = pl.col("count").log()
)


chart = (
    alt.Chart(kanjis_count.to_pandas())
    .mark_rect()
    .encode(
        alt.Y("count_readings_on:O", title="On'yomi"),
        alt.X("count_readings_kun:O", title="Kun'yomi", axis=alt.Axis(labelAngle=0)),
        alt.Color("count_log",title="Logarithm of the total", scale=alt.Scale(scheme='cividis'))
    )
).properties(
    title="Heatmap of the readings in Kun'yomi (japanese reading) and On'yomi (original chinese reading)",
    height = 500,
    width = 660
)
col1,col2 = st.columns([5,3], gap="large") # creates n_cols spaces where to put each df

with(col1):
    st.altair_chart(chart)
with(col2):
    st.write("###### Analysis:")
    st.write(
        '''
        The heatmap shows the amount of Kun'yomi and On'yomi readings per kanji, differentiated by the colors,
        representing the logarithm of the total amount of kanjis with the respective combination.  

        The most common kanjis, numbering around 3000, typically have one Kun'yomi and one On'yomi reading.  
        Though there are several cases where a unique kanji has a specific combination of readings.  

        Additionally, many kanjis in the dataset lack readings in both categories due to insufficient data.

        But overall it's still highligthed the distribution of the readings,
        where most kanjis tend to have a total of 6 readings, divided in one or the other type.

        ''')


st.write(
    '''
    ---  
    ---
    ''')
######### Graph of kanjis and radicals ###########

st.write("### Graph of kanjis and radicals")
st.write("The graph shows the connections between the most used 125 kanjis and their respective radicals")
st.info("You can move or increase/decrease the field of view by dragging and scrolling")


# keep only the most used kanjis (for clearer and faster to load results)
kanjis_filtered = (
    kanjis
    .filter(pl.col("freq") < 30) # recommended 125 kanjis for a good balance of quantity and readability 
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
net = Network(bgcolor="#E0FFFF") # #E0FFFF == LightCyan

# add nodes for kanji and radicals
for kanji, radicals in kanjis_filtered.iter_rows():

    # add kanji node
    net.add_node(kanji, label=kanji, color='#FF00FF', size=10) # #FF00FF == fuchsia
    
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
            background-color: #E0FFFF; 
            color: black;
            width: 115px;
        ">
            <h4 style="margin-top: 0;">Legend:</h4>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 12px; height: 12px; background-color: navy; border-radius: 50%; margin-right: 5px"></div>
                <span>Radicals</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 12px; height: 12px; background-color: #FF00FF; border-radius: 50%; margin-right: 5px;"></div>
                <span>Kanjis</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )




