
import json                 # read json file
import polars as pl
import streamlit as st
import pandas as pd         # to_csv(mode='a')
import os                   # cehck if file exists

# url = https://github.com/davidluzgouveia/kanji-data

kanji_url = r'C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\kanji.json'
with open(kanji_url, 'r', encoding="UTF-8" ) as file:
    data = json.load(file)

## print( pl.read_json(kanji_json).head()) # formato del file non adatto per read_json

kanjis_raw = list()
for kanji in data: # for every kanji in the file, each with its data
    kanji_dict = {"character": kanji} # convert the kanji to an item in a dict
    kanji_dict.update(data[kanji]) 
    kanjis_raw.append(kanji_dict) # append the new dict of the kanji

# Create a Polars DataFrame from the list of dictionaries, with only the useful columns
kanjis = pl.DataFrame(kanjis_raw).select(
    pl.col(["character", "meanings","readings_on","wk_meanings", "wk_radicals"])
    )

# '''print("Total number of kanjis in the df: ",kanjis.select(pl.count("character")))
# 13108

# words_tsv = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\words.tsv"
# words = pl.read_csv(words_tsv, separator="\t")


# search for words with a kanji in them
# char_search = kanjis.item(80,"character")
# print(
#     f"Words with the kanji {char_search} in them:\n",
#     words
#     .filter(
#         pl.col("word or phrase")
#         .str.contains( char_search )
#         )
#     )
# '''






# Note: Some of the meanings and readings that were extracted from WaniKani have a ^ or a ! prefix.
# I added these to denote when an item is not a primary answer (^) or not an accepted answer (!) on WaniKani. 



# Find the corrresponding kanji of an english word
def kanji_search(word_search):
    # The dataframe's english words are formatted as capitalized
    word_search = word_search.lower().capitalize()

    # a double confirmation is necessary since in the df a single kanji has a primary meaning and different secondary meanings
    df = kanjis.filter(
        # check if the word is in the "meanings" column
        pl.col("meanings").list.contains(word_search)

        &

        # check if the word is in the "wk_meanings" column
        (  
            pl.col("wk_meanings").list.contains(word_search)
            |
            pl.col("wk_meanings").list.contains(f"^{word_search}") # easier then removing the '^' from the words in the df
        )
    )
    return df
    

# '''search_word = input("Insert word to search the kanji/s of: ")
# search_df = kanji_search(search_word)
# print(search_df)
# '''



############# Streamlit ###############

# file with the saved kanjis library
saved_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\saved.tsv"

# Title
st.write('# Kanji search')

# User chooses the word to search and return the df with the corresponding kanjis
search_word = st.text_input("Insert word to search: ")
search_df = kanji_search(search_word).with_columns(
    save = pl.lit(False) # add a save column, to save the kanji in the library
)

# create a checkbox in the save column
search_df_edit = pl.DataFrame(st.data_editor( # returns a pandas df
    search_df,
    column_config={
        "save": st.column_config.CheckboxColumn(
            "save?",
            default=False # checkbox is initially not checked
        )
    },
    disabled=["character", "meanings","readings_on","wk_meanings", "wk_radicals"]
))




#######################

# if the file doesn't exists it initializes it with a kanji as example
def initialize_file():
    if not os.path.exists(saved_url):
        row0 = pd.DataFrame(kanjis.head(1)) # example kanji df
        row0['save'] = True # add the save column to it

        # creates the library file and writes the header
        with open(saved_url, mode="w") as f:
            f.write('character\tmeanings\treadings_on\twk_meanings\twk_radicals\tsave\n')
        
        # append the example dataframe
        row0.to_csv(saved_url, mode="a", sep="\t" ,header=False, index=False)

# Initialize the file if missing
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
    disabled=["character", "meanings","readings_on","wk_meanings", "wk_radicals"]
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





