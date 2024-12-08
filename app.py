
#
# cambia nome colonna character ?
# mettere False nel save di phrases
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

# Trovare kanji per pronuncia

import json                 # read json file
import polars as pl
import streamlit as st
import pandas as pd         # to_csv(mode='a')
import os                   # cehck if file exists

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

        romaji_word = ''.join(kana_dict.get(char, '') for char in word) ##### toglie il punto
        new_row.append(romaji_word)
    return new_row

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

    # Gets the word/s with the clear desired meaning
    df = kanjis.filter(meanings & wk_meanings)
    # A double confirmation is necessary since in the df a single kanji has a primary meaning and different secondary meanings

    # Gets the word/s with a less clear desired meaning
    if df.is_empty():
        df = kanjis.filter(meanings | wk_meanings)
    
    if df.is_empty():
        df = kanjis.filter(
            pl.col("meanings").list.contains(word_search.lower())
        )
    
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
            "save?",
            default=False # checkbox is initially not checked
        )
    },
    use_container_width=True,
    column_order=("save","character","meanings","wk_meanings", "readings_on","readings_kun","wk_radicals"),
    disabled=["character", "meanings","readings_on","wk_meanings", "wk_radicals"]
))




# file with the saved kanjis library
saved_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\saved.tsv"

# if the file doesn't exists it initializes it with a kanji as example
# st.write(kanjis.columns)
kanjis_col_all = 'save'
for i in kanjis.columns[2:]:
    kanjis_col_all = kanjis_col_all +'\t' + i 

# a = pd.DataFrame(kanjis.head(1))
# a.insert(loc = 0,column='save',value=True)
# st.write(a)

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

# reads the library file
saved = pl.read_csv(saved_url, separator='\t',truncate_ragged_lines=True)

st.write("Saved kanjis library: ")
# adds the checkbox to the 'save' column and prints the df
saved_edit = pl.DataFrame(st.data_editor( # returns a pandas df
    saved,
    column_config={
        "save": st.column_config.CheckboxColumn(
            "save?",
            default=True
            # if a kanji is in the library, it means it was checked in the
            # search dataframe earlier, so the checkbox is checked by default
        )
    },
    use_container_width=True,
    column_order=("save","character","meanings","wk_meanings", "readings_on","readings_kun","wk_radicals"),
    disabled=("character","meanings","wk_meanings", "readings_on","readings_kun","wk_radicals")
))

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


# If a kanji in the library is unchecked, it removes it
if not (saved_edit["save"].all()):

    # makes the dataframe with only the checked kanjis the new saved library
    saved_edit_post_remove = saved_edit.filter(
            pl.col("save") == True
        )
    
    # overwrites the save file without the unchecked kanjis
    saved_edit_post_remove.write_csv(saved_url, separator="\t", include_header=True)








#############################

# Same radicals in saved kanjis

search_radical = st.text_input("Search for saved kanjis with the same radical:").lower().capitalize()

saved_radicals = saved.filter(pl.col("wk_radicals").str.contains(search_radical))
if(search_radical):
    st.write(saved_radicals)






#########

# Analysis

import altair as alt



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

test = kanjis_count.group_by(pl.col(["jlpt_new","strokes"])).agg(pl.col("character").count()).filter(~pl.col("jlpt_new").is_null())

chart = (
    alt.Chart(test)
    .mark_circle()
    .encode(
        alt.Y("jlpt_new:N"),
        alt.X("strokes"),
        alt.Size("character",title="Number of kanjis")
    )
).properties(
    height = 200,
    width = 480
)
st.write("Amount of kanjis for jlpt level and number of strokes")
st.altair_chart(
    chart
)