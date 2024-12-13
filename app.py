
# Bug: Se tolgo un kanji che nel search df ha la checkbox true -> lo risalva
# - mettere che se metto true lo rimette subito a False ?
# Nella ricerca per cana non conta i tsu piccoli (dako -> dakko)

# cambia nome colonna character ?
# Questione lower, forse meglio cercare di rendere tutto minuscolo in kanjis ? Forse no ?
# - fare in modo che trova parole lunghe insieme ai singoli kanji, non solo se non ne trova (?) # es. plane (hikouki)
# tenere words_load così o più compatto ?
# mostrare salvati solo il kanji e poi se ci passi sopra/clicchi/.. mostra i dettagli e grafici(?)
# - metterlo come cambio di modalità in cui si vede il df a scelta dell'utente
# - mettere lista a cascata dei kanji e il selezionato mostra il dataset
# Fai sezione aperta da un pulsante dei grafici / analisi dei kanji
# cerca kanji con radicale uguale
# cerca parole con lo stesso kanji dentro
# unire romaji a df originale ?

# grafo cluster di radicali più usati 
# (aggiungere radicali mancanti ?)

# Trovare kanji per pronuncia

import json                 # read json file
import polars as pl
import streamlit as st
import pandas as pd         # to_csv(mode='a')
import os                   # cehck if file exists
import altair as alt
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
# url = https://github.com/davidluzgouveia/kanji-data




###########
# kanji.json

st.set_page_config(layout="wide")

kanji_url = r'C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\kanji.json'

@st.cache_data
def kanji_load():
    with open(kanji_url, 'r', encoding="UTF-8" ) as file:
        data = json.load(file)
    ## print( pl.read_json(kanji_json).head()) # formato del file non adatto per read_json
    kanjis_raw = list()
    for kanji in data: # for every kanji in the file, each with its data
        kanji_dict = {"save": False,"character": kanji} # convert the kanji to an item in a dict
        kanji_dict.update(data[kanji]) 
        kanjis_raw.append(kanji_dict) # append the new dict of the kanji

    # st.write(pl.DataFrame(kanjis_raw))
    # kanjis = pl.DataFrame(kanjis_raw).with_columns(
    #     pl.col(["meanings","wk_meanings","wk_radicals"]).str.to_lowercase()
    #     )

    return pl.DataFrame(kanjis_raw)

kanjis = kanji_load()
# print("Total number of kanjis in the df: ",kanjis.select(pl.count("character")))
# 13108




# Note: Some of the meanings and readings that were extracted from WaniKani have a ^ or a ! prefix.
# I added these to denote when an item is not a primary answer (^) or not an accepted answer (!) on WaniKani. 




################
# words.tsv

words_tsv = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\words.tsv"


@st.cache_data
def words_load():
    phrases = (
        pl.read_csv(words_tsv, separator="\t")
        .rename({"word or phrase": "character", "kana": "readings_kun", "translation": "meanings", "tags": "jlpt_new"})
    
        # keep only the phrases with more than 1 kanji in them (since most likely all of them are already in the kanjis df)
        .filter( pl.col("character").str.len_chars() > 1 )
    )
    # keep only the jlpt value from the orignally "tags" column of the words df
    phrases = phrases.with_columns(
        # turn all thes strings in the column to lowercase
        # pl.col("meanings").str.to_lowercase(),

        pl.col("jlpt_new").str.split("|")
        .list.eval(
            pl.element().filter(
                pl.element().is_in(["n1","n2","n3","n4","n5"])
                )
            ).list.first().str.strip_chars('n').cast(pl.Int64)
        )

    phrases = phrases.with_columns(
        # transform the string columns into list of strings, like in the respective kanjis df columns 
        pl.col(["meanings","readings_kun"]).str.split(", "),

        # make the save column a boolean with False values like the respective kanjis df column
        save = pl.lit(False)
    )

    # adds the missing columns of the phrases df, to be able to stack the 2 dfs
    phrases = (
        phrases
        .with_columns(
            # for every column of the kanjis df not in the words df, it adds a column with the same name of NULLs 
            pl.lit(None).alias(col) for col in kanjis.columns if col not in phrases.columns
            )
            # sorts the columns in the correct order
            .select(kanjis.columns)
    )
    return phrases

phrases = words_load()
kanjis = kanjis.vstack(phrases)


##################

kana_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\kana.json"

# load the kana file
@st.cache_data
def kana_load():
    with open(kana_url, mode="r") as f:
        json_object = json.load(f)
    return json_object

# dict where keys = kana, values = romaji (spelling in the roman alphabet)
kana_dict = kana_load()

# given a list of kanas, it translates it to romaji
def kana_to_romaji(row):
    new_row = []
    for word in row:
        romaji_word = ''.join(kana_dict.get(char, '') for char in word)
        new_row.append(romaji_word)
    return new_row

# adds the romaji translation to the kanjis df (creates a new different df)
@st.cache_data
def add_romaji():
    return kanjis.with_columns(
        romaji_on = pl.col("readings_on").map_elements(kana_to_romaji, return_dtype = pl.List(pl.String)),
        romaji_kun = pl.col("readings_kun").map_elements(kana_to_romaji, return_dtype = pl.List(pl.String))
    )

kanjis_romaji = add_romaji()


# st.write("Romaji: ")
# kanjis_romaji


################

# Find the corrresponding kanji of an english word
def kanji_search(word_search):
    # The dataframe's english words are formatted as capitalized
    word_search = word_search.lower().capitalize()

    # check if the word is in the "meanings" column
    meanings = pl.col("meanings").list.contains(word_search)
    
    # check if the word is in the "wk_meanings" column
    wk_meanings = (
        pl.col("wk_meanings").list.contains(word_search)
        |
        pl.col("wk_meanings").list.contains(f"^{word_search}") # easier then removing the '^' from the words in the df
    )

    # gets the word/s with the clear desired meaning
    df = kanjis.filter(meanings & wk_meanings)
    # A double confirmation is necessary since in the df a single kanji has a primary meaning and different secondary meanings

    # gets the word/s with a less clear desired meaning
    if df.is_empty():
        df = kanjis.filter(meanings | wk_meanings)
    
    # gets the words composed of multiple kanjis
    if df.is_empty():
        df = kanjis.filter(
            pl.col("meanings").list.contains(word_search.lower())
        )
    
    # gets the kanjis if the word search was in romaji 
    if df.is_empty():
        df = kanjis_romaji.filter(
            pl.col("romaji_on").list.contains(word_search.lower())
            |
            pl.col("romaji_kun").list.contains(word_search.lower())
        )


    return df
    







    

############# Streamlit ###############

# Title
st.write('# Kanji search')

# User chooses the word to search and return the df with the corresponding kanjis
search_word = st.text_input("Insert word to search: ")
search_df = kanji_search(search_word)

# create a checkbox in the save column

search_df_edit = pl.DataFrame(st.data_editor( # returns a pandas df
    search_df,
    column_config={
        "save": st.column_config.CheckboxColumn(
            default=False # checkbox is initially not checked
        )
    },
    use_container_width=True,
    column_order=("save","character","meanings","wk_meanings", "readings_on","readings_kun","wk_radicals"),
    disabled=["character", "meanings","readings_on","wk_meanings", "wk_radicals"]
))
# search_df_edit = search_df_edit.with_columns(
#     pl.lit(False).alias("save")
# )



# file with the saved kanjis library
saved_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\saved.tsv"

# if the file doesn't exists it initializes it with a kanji as example
# st.write(kanjis.columns)
kanjis_col_all = 'save'
for i in kanjis.columns[1:]:
    kanjis_col_all = kanjis_col_all +'\t' + i 


def initialize_file():
    if not os.path.exists(saved_url):
        row0 = pd.DataFrame(kanjis.head(1)) # example kanji df
        row0['save'] = True
        # row0['save'] = True # add the save column to it
        # st.write(row0)

        # creates the library file and writes the header
        with open(saved_url, mode="w") as f:
            f.write(kanjis_col_all + "\n")
        
        # append the example dataframe
        row0.to_csv(saved_url, mode="a", sep="\t" ,header=False, index=False)

# Initialize the file if missing
if not os.path.exists(saved_url):
    initialize_file()



##################################

# reads the library file
saved = pl.read_csv(saved_url, separator='\t',truncate_ragged_lines=True)

# switches to the compact viewing mode
is_compact = st.checkbox("Compact viewing style")

if(is_compact):
    # Instead of showing all the info of each saved kanji, it shows only the 'save' and 'character' columns
    # And to view all the info you check a checkbox of the kanjis the user chooses

    st.write("Saved kanjis library - Compact:")

    # create pandas df with only 'save' and 'character' column, to use less space
    kanjis_pd = (
        saved
        .select(pl.col(["save","character"]))
        .to_pandas() # needed in pandas for the AgGrid functions
        ).astype({'character': 'string'}) # pandas reads the 'character' column as an 'object' type

    
    n_cols = 6 # number of df to fit next to each other
    cols = st.columns(n_cols) # creates n_cols spaces where to put each df

    n_kanjis = 5 # initial number of kanjis per df 
    height_kanjis_pd = 175 # height of the df needed to fit 5 rows of kanjis

    # increases the amount of kanjis per df if there are too many to fit with the previous amount 
    while(len(kanjis_pd) > n_kanjis * n_cols):
        n_kanjis += 5 # adds the space for 5 kanjis per each df
        height_kanjis_pd += 140 # every +140 adds 5 rows of kanjis
    
    # split the dataframe into smaller ones containing up to 'n_kanjis' kanjis
    kanjis_split = []
    for i in range(0, len(kanjis_pd), n_kanjis): 
        kanjis_split.append(kanjis_pd.iloc[i : i + n_kanjis])

    grid_data_list = [] # will contain all the ["data"] parts of the AgGrid objects 
    grid_selection_list = [] # will contain all the ["selected_rows"] parts of the AgGrid objects 

    for i in range(len(kanjis_split)): # for each dataframe
        with cols[i]:
            # setup for the saved kanjis df
            gb = GridOptionsBuilder.from_dataframe(kanjis_split[i]) # requires a pandas df
            gb.configure_selection("multiple", use_checkbox = True)  # Allows more than 1 row to be selected with a checkbox (without doesn't allow multiple selection and deselection)
            gb.configure_column("save", editable=True)  # Allow editing of the "save" checkbox
            gb.configure_column("character", editable=False, cellRenderer="agGroupCellRenderer")  # Make "character" non-editable but clickable by the user
            grid_options = gb.build() # makes checkboxes clickable

            # creates and shows the saved kanjis df
            grid_response = AgGrid(
                kanjis_split[i],
                gridOptions = grid_options, 
                update_mode = GridUpdateMode.SELECTION_CHANGED,
                height = height_kanjis_pd,
                theme = "streamlit",
                # allow_unsafe_jscode = True,
            )

            # adds each splitted df to a list
            grid_data_list.append(pl.DataFrame(grid_response["data"]))

            # adds to a list the rows selected by the user
            selection = pl.DataFrame(grid_response["selected_rows"])
            if not selection.is_empty():
                grid_selection_list.append(selection)

    # if at least 1 kanji is in the saved library
    if len(grid_data_list) > 0:
        # concatenates the splitted dataframes into 1
        grid_data_df = pl.concat(grid_data_list) 
        
        # adds the remaning columns to the df (only has 'save' and 'character' columns)
        saved_edit = grid_data_df.join(kanjis.drop("save"), on="character")

    else:
        # initialize the saved_edit df as an empty dataframe with the kanjis df's header
        saved_edit = kanjis.head(1).filter(False)
    
    # if at least 1 kanji was selected
    if len(grid_selection_list) > 0:
        grid_selection_df = pl.concat(grid_selection_list) # concatenate the dataframes in the list

        # shows all the selected kanjis with all their informations
        for i in range(len(grid_selection_df)):
            selected_kanji = grid_selection_df.row(i)[1]
            st.write(f"# {selected_kanji}", kanjis.filter(pl.col('character') == selected_kanji))


# Normal mode
else:
    st.write("Saved kanjis library: ")
    # adds the checkbox to the 'save' column and prints the df
    saved_edit = pl.DataFrame(st.data_editor( # returns a pandas df
        saved,
        column_config={
            "save": st.column_config.CheckboxColumn(
                default=True
                # if a kanji is in the library, it means it was checked in the
                # search dataframe earlier, so the checkbox is checked by default
            )
        },
        use_container_width=True,
        column_order=("save","character","meanings","wk_meanings", "readings_on","readings_kun","wk_radicals"),
        disabled=("character","meanings","wk_meanings", "readings_on","readings_kun","wk_radicals")
    ))






##################### add and remove kanjis from the saved library ##################

# df with the kanjis checked in the search df, that need to be added to the library
kanji_to_add = search_df_edit.filter(
    # get the rows with kanjis that aren't already in the library
    ~pl.col("character").is_in(saved_edit.select(pl.col("character")))
    ).filter( # of the remaning row gets the ones with a checked box
        pl.col("save") == True
    )

# adds the kanjis to the library, if there are any to add
if not kanji_to_add.is_empty():
    pd.DataFrame(kanji_to_add).to_csv(saved_url, mode="a", index=False, header=False, sep="\t")
    st.rerun() 




# If a kanji in the library is unchecked, it removes it
if not saved_edit.is_empty(): # without it gives an error for the next if 
    if not saved_edit["save"].all():

        # makes the dataframe with only the checked kanjis the new saved library
        saved_edit_post_remove = saved_edit.filter(
                pl.col("save") == True
            )

        # overwrites the save file without the unchecked kanjis
        saved_edit_post_remove.to_pandas().to_csv(saved_url, sep="\t",index=False, header=True)
        ## saved_edit_post_remove.write_csv(saved_url, separator="\t", include_header=True) # write_csv doesn't work with nested data

        st.rerun() 




############## Operations on the saved kanjis ###############

# Gets the saved kanjis with the same radical

search_radical = st.text_input("Search for saved kanjis with the same radical:").lower().capitalize()

saved_radicals = saved.filter(pl.col("wk_radicals").str.contains(search_radical))
if(search_radical):
    st.write(saved_radicals)








###################### Plots ##########################


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
jlpt_strokes
chart = (
    alt.Chart(jlpt_strokes.to_pandas())
    .mark_circle()
    .encode(
        alt.Y("jlpt_new:O", sort="descending"),
        alt.X("strokes"),
        alt.Size("character", title="Number of kanjis"),
    )
).properties(
    height = 200,
    width = 480
)
st.write("Amount of kanjis for jlpt level and number of strokes")

st.altair_chart(chart)
# The more difficult the level the more strokes are needed
# there seems to be somewhat of a normal distribution among all levels, getting clearer with the increase in difficulty (and in amount of kanjis)







###################################################

from sklearn.cluster import KMeans
from sklearn.preprocessing import MultiLabelBinarizer
import numpy as np

# Sample dataframe of Kanji and their radicals
# data = {
#     "character": kanjis.select(pl.col("character")).explode("character"),
#     "wk_radicals": kanjis.select(pl.col("wk_radicals")).explode("wk_radicals")
# }

# df = pd.DataFrame(data)
# df
df = pd.DataFrame(
    kanjis
    .filter(~pl.col("wk_radicals").is_null())
    .select(pl.col(["character","wk_radicals"]))
    ) #.rename( columns = {"0":"character","1": "wk_radicals"})
df.columns = ["Kanji","Radicals"]
df

# Encode radicals with MultiLabelBinarizer
mlb = MultiLabelBinarizer()
radicals_encoded = mlb.fit_transform(df["Radicals"])
radicals_df = pd.DataFrame(radicals_encoded, columns=mlb.classes_)

# Compute the frequency of each radical
radical_frequencies = radicals_df.sum(axis=0)

# Create a DataFrame for clustering
freq_df = pd.DataFrame({
    "Radical": radical_frequencies.index,
    "Frequency": radical_frequencies.values
})

# Perform clustering on radical frequencies
kmeans = KMeans(n_clusters=5, random_state=42)
freq_df["Cluster"] = kmeans.fit_predict(freq_df[["Frequency"]])

# Visualize the clustered radical frequencies
chart = alt.Chart(freq_df).mark_bar().encode(
    x=alt.X('Radical:N', title="Radical"),
    y=alt.Y('Frequency:Q', title="Frequency"),
    color=alt.Color('Cluster:N', title="Cluster"),
    tooltip=['Radical', 'Frequency', 'Cluster']
).properties(
    title="Radical Frequency and Clustering"
)

# chart.show()
st.altair_chart(
    chart
)

# from sklearn.cluster import KMeans
# from sklearn.preprocessing import MultiLabelBinarizer

# # Sample data of Kanji and their radicals
# df = kanjis.select(pl.col(["character","wk_radicals"]))
# df
# # Expand multiple radicals using MultiLabelBinarizer
# mlb = MultiLabelBinarizer()
# radicals_encoded = mlb.fit_transform(df["wk_radicals"].to_list())
# radicals_df = pl.DataFrame(radicals_encoded, schema=mlb.classes_)

# # Add encoded radicals back to the Polars dataframe
# df_encoded = df.hstack(radicals_df)

# # Perform k-means clustering using the encoded data
# kmeans = KMeans(n_clusters=3, random_state=42)
# clusters = kmeans.fit_predict(radicals_encoded)

# # Add cluster labels to the Polars dataframe
# df_encoded = df_encoded.with_columns(pl.Series("Cluster", clusters))

# # Convert Polars DataFrame to Pandas for Altair compatibility
# df_pandas = df_encoded.to_pandas()

# # Create a scatter plot using Altair
# chart = alt.Chart(df_pandas).mark_circle(size=100).encode(
#     x=alt.X('character:N', title="Kanji"),
#     y=alt.Y('Cluster:N', title="Cluster"),
#     color=alt.Color('Cluster:N', title="Cluster"),
#     tooltip=['character', 'wk_radicals', 'Cluster']
# ).properties(
#     title="Kanji Cluster Analysis with Polars"
# )

# # chart.show()
# st.altair_chart(
#     chart
# )

#########################################################


# most used radicals


# radicals_count_dict = radicals_count.set_index('wk_radicals').to_dict()['count']
import streamlit as st
import pyvis
from pyvis.network import Network
import polars as pl

# Example DataFrame (Replace with your actual data)
# data = {
#     "character": ["一", "二", "三", "四"],
#     "wk_radicals": [["一"], ["二"], ["三"], ["一", "二"]]
# }

# # Create a Polars DataFrame
# kanjis = pl.DataFrame(data)
kanjis_filtered = (
    kanjis
    .filter(
        ~pl.col("freq").is_null()
        &
        ~pl.col("wk_radicals").is_null()
    )
    .filter(pl.col("freq") < 100)

    .sort(pl.col("freq"))
    .select(pl.col(["character", "wk_radicals"])) 
)

radicals_count = (
    kanjis_filtered
    .select(pl.col("wk_radicals")).explode("wk_radicals")
    .select(pl.col("wk_radicals").value_counts())
    .unnest("wk_radicals")
    .sort(by="count",descending=True)
).filter(~pl.col("wk_radicals").is_null())
radicals_count_norm = (
    radicals_count
    .with_columns(
        count = pl.col("count") / pl.col("count").max()
        )
    )

radicals_count_dict = dict(zip(radicals_count['wk_radicals'], radicals_count_norm['count']))


# Initialize PyVis Network
net = Network(notebook=False)

# Add nodes for Kanji and radicals
for kanji, radicals in kanjis_filtered.iter_rows():

    # Add Kanji node
    net.add_node(kanji, label=kanji, color='red', size=10)
    
    # Add radical nodes and edges
    for radical in radicals:

        # Add radical node
        net.add_node(radical, label=radical, color='blue', size=radicals_count_dict[radical]*30)
        # Add edge between Kanji and radical
        net.add_edge(kanji, radical)

# Save the network as an HTML file
output_path = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\simple_network.html"
net.save_graph(output_path)

# Display the graph in Streamlit using st.components.v1.html
with open(output_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Embed the HTML content into Streamlit
st.components.v1.html(html_content, height=600)







#################
from pyvis.network import Network
import networkx as nx

# Example data
import pandas as pd


import networkx as nx
import matplotlib.pyplot as plt



# # Create a simple graph
# G = nx.Graph()
# G.add_edge(1, 2)

# # Draw the graph
# nx.draw(G, with_labels=True)
# st.pyplot(plt)

# st.write("bbbbbbbbbbbbbbb")



from pyvis.network import Network

# Initialize PyVis Network (disable notebook rendering to avoid notebook-specific errors)
# net = Network(notebook=False)

# # Add nodes and edges
# net.add_node(1, label="Node 1")
# net.add_node(2, label="Node 2")
# net.add_edge(1, 2)

# # Save the network as an HTML file
# output_path = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\simple_network.html"
# net.save_graph(output_path)

# # Display the graph in Streamlit using st.components.v1.html
# with open(output_path, "r", encoding="utf-8") as f:
#     html_content = f.read()

# # Embed the HTML content into Streamlit
# st.components.v1.html(html_content, height=600)



# Kanji and their radicals (replace this with your actual data)
data = pd.DataFrame({
    "character": ["木", "森", "林"],
    "radicals": [["木"], ["木", "木", "木"], ["木", "木"]]
})

# Create a graph object using NetworkX
G = nx.Graph()

# Add edges between kanji and radicals
for index, row in data.iterrows():
    kanji = row["character"]
    for radical in row["radicals"]:
        G.add_edge(kanji, radical)

# Initialize PyVis Network
net = Network(notebook=False, height="750px", width="100%", directed=False)

# Load the NetworkX graph into PyVis
net.from_nx(G)

# Save and show the visualization

net.show("kanji_radical_network.html")

# Read the HTML file and embed it in Streamlit
with open("kanji_radical_network.html", "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=750, width=900)
#############################
# # Assuming `kanjis` is your original dataframe with a "freq" column
# kanjis_filtered = (
#     kanjis
#     .filter(
#         ~pl.col("freq").is_null()
#         &
#         ~pl.col("wk_radicals").is_null()
#     )
#     .sort(pl.col("freq"))
#     .select(pl.col(["character", "wk_radicals"])) 
# )

# kanjis_filtered
# # Create edges: Each kanji-radical pair
# edges = (
#     kanjis_filtered
    
#     .explode("wk_radicals")
#     .rename({"character": "kanji", "wk_radicals": "radical"})
# )

# # Create nodes: Combine unique kanjis and radicals
# kanji_nodes = edges.select(pl.col("kanji").unique()).rename({"kanji": "node"}).with_columns(
#     pl.lit("kanji").alias("type")
# )
# radical_nodes = edges.select(pl.col("radical").unique()).rename({"radical": "node"}).with_columns(
#     pl.lit("radical").alias("type")
# )
# nodes = pl.concat([kanji_nodes, radical_nodes])

# # Assign simple positions and sizes for visualization
# nodes = nodes.with_columns([
#     (pl.col("type") == "kanji").cast(int).alias("x"),  # kanji = 1, radical = 0
#     pl.arange(0, nodes.height).alias("y"),  # simple unique y positions
#     pl.when(pl.col("type") == "kanji").then(40).otherwise(20).alias("size")  # size based on type
# ])

# # Convert to pandas for Altair
# nodes_pd = nodes.to_pandas()
# edges_pd = edges.to_pandas()

# # Create edges chart
# edges_chart = alt.Chart(edges_pd).mark_line(opacity=0.6, strokeWidth=1).encode(
#     x=alt.X('kanji:N', title='Kanji'),
#     x2=alt.X2('radical:N', title='Radical'),
# )

# # Create nodes chart
# nodes_chart = alt.Chart(nodes_pd).mark_circle().encode(
#     x='x:Q',
#     y='y:Q',
#     size='size:Q',
#     color='type:N',
#     tooltip='node:N'
# )

# # Combine charts
# network_chart = edges_chart + nodes_chart
# network_chart = network_chart.properties(width=600, height=400)

# # Display in Streamlit
# st.altair_chart(network_chart, use_container_width=True)

