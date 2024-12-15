
# Bug: Se tolgo un kanji che nel search df ha la checkbox true -> lo risalva
# - mettere che se metto true lo rimette subito a False ?
# Nella ricerca per cana non conta i tsu piccoli (dako -> dakko)

# cambia nome colonna character ?
# Questione lower, forse meglio cercare di rendere tutto minuscolo in kanjis ? Forse no ?
# - fare in modo che trova parole lunghe insieme ai singoli kanji, non solo se non ne trova (?) # es. plane (hikouki)
# tenere words_load così o più compatto ?

# Fai sezione aperta da un pulsante dei grafici / analisi dei kanji
# cerca kanji con radicale uguale
# cerca parole con lo stesso kanji dentro
# unire romaji a df originale ?

# grafo cluster di radicali più usati 
# (aggiungere radicali mancanti ?)


import json                 # read json file
import polars as pl         # data manipulation
import streamlit as st      # framework to create an interactive app
import pandas as pd         # used for functions that won't work with polars
import os                   # cehck if save kanjis file exists
import altair as alt        # make plots
from st_aggrid import AgGrid, GridOptionsBuilder # allow dataframe to be clickable
from st_aggrid.shared import GridUpdateMode
# import pyvis
from pyvis.network import Network
# Data sources:
# https://github.com/davidluzgouveia/kanji-data  ## kanji.json
# https://www.kaggle.com/datasets/dinislamgaraev/popular-japanese-words ## words.tsv



################ Load and clean Data ################

# configures the streamlit page layout
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

    return pl.DataFrame(kanjis_raw)

kanjis = kanji_load() # 13108 kanjis


# Note from the source data author: "Some of the meanings and readings that were extracted from WaniKani have a ^ or a ! prefix.
# I added these to denote when an item is not a primary answer (^) or not an accepted answer (!) on WaniKani"


################

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

# dictionary {kana: romaji}
# kana: japanese phonetic alphabet 
# romaji: translation of kana in the latin alphabet phontics 
kana_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\kana.json"

# load the kana file
# @st.cache_data
def kana_load():
    with open(kana_url, mode="r") as f:
        json_object = json.load(f)
    return json_object

# dict where keys = kana, values = romaji (spelling in the roman alphabet)
kana_dict = kana_load()

# given a list of kanas, it translates it to romaji
def kana_to_romaji(row):
    new_row = []
    double_letter = False
    for word in row:
        romaji_word = ''
        for char in word:
            if char in ["ゃ", "ゅ", "ょ","ャ", "ュ", "ョ"]:
                romaji_word = romaji_word[:-1]

            if double_letter:
                romaji_word = romaji_word + kana_dict.get(char, '')[0]
                double_letter = False
            
            romaji_word = romaji_word + kana_dict.get(char, '')
            
            if char == "っ":
                double_letter = True

        

        new_row.append(romaji_word)
    return new_row
# st.write(kana_to_romaji(["きゅう","く"]))
# adds the romaji translation to the kanjis df (creates a new different df)
@st.cache_data
def add_romaji():
    return kanjis.with_columns(
        romaji_on = pl.col("readings_on").map_elements(kana_to_romaji, return_dtype = pl.List(pl.String)),
        romaji_kun = pl.col("readings_kun").map_elements(kana_to_romaji, return_dtype = pl.List(pl.String))
    )

kanjis_romaji = add_romaji()
kanjis_romaji
a

#############################

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

# User chooses the word to search and returns the df with the corresponding kanji/s
search_word = st.text_input("Insert word to search: ")
search_df = kanji_search(search_word)

# create a checkbox in the save column
search_df_edit = pl.DataFrame(st.data_editor( # returns a pandas df by default
    search_df,
    column_config={
        "save": st.column_config.CheckboxColumn(
            default=False # checkbox is initially not checked
        )
    },
    use_container_width=True,
    column_order=("save","character","meanings","wk_meanings","readings_on","readings_kun","wk_radicals"),
    disabled=["character","meanings","wk_meanings","readings_on","readings_kun","wk_radicals"]
))





# file with the saved kanjis library
saved_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\saved.tsv"


def initialize_file():
    (
        kanjis
        .head(1).filter(False) # keep only the header of the dataframe
        .to_pandas()
        .to_csv(saved_url, sep="\t", header=True, index=False)
    )

# Initialize the file if it doesn't yet exists
if not os.path.exists(saved_url):
    initialize_file()



############### Saved Kanjis Library ###################

# reads the kanjis library file
saved = pl.read_csv(saved_url, separator='\t',truncate_ragged_lines=True)

# switches to the compact viewing mode
is_compact = st.checkbox("Compact viewing style")

# Normal mode
if not(is_compact):
    st.write("Saved kanjis library:")
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

# Compact mode
else:
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








##################### Add and remove kanjis from the saved library ##################

### Add ###

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



### Remove ###

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

# there seems to be somewhat of a normal distribution among all levels,
# getting clearer with the increase in difficulty (and in amount of kanjis)







###################################################

# most used radicals

# keep only the most used kanjis (for clearer and faster to load results)
kanjis_filtered = (
    kanjis
    .filter(pl.col("freq") < 100)
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
net = Network(bgcolor="black", font_color="white")

# add nodes for kanji and radicals
for kanji, radicals in kanjis_filtered.iter_rows():

    # add kanji node
    net.add_node(kanji, label=kanji, color='red', size=10)
    
    # add radical nodes and edges
    for radical in radicals:

        # add radical node
        net.add_node(radical, label=radical, color='blue', size=radicals_count_dict[radical]*30)
        # add edge between kanji and radical
        net.add_edge(kanji, radical)

# save the network as an HTML file
output_path = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\simple_network.html"
net.save_graph(output_path)

# read the html file
with open(output_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# show the plot in Streamlit
st.components.v1.html(html_content, height=600)


