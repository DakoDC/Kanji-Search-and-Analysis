
import json
import polars as pl
import streamlit as st

# url = https://github.com/davidluzgouveia/kanji-data

kanji_json = r'C:\Users\dakot\OneDrive\Desktop\Git repositories\Kanji-Analysis\kanji.json'
with open(kanji_json, 'r', encoding="UTF-8" ) as file:
    data = json.load(file)

# print( pl.read_json(kanji_json).head()) # formato del file non adatto per read_json

new_data = list()
for kanji in data: # for every kanji in the file, each with its data
    kanji_dict = {"character": kanji} # convert the kanji to an item in a dict
    kanji_dict.update(data[kanji]) 
    new_data.append(kanji_dict) # append the new dict of the kanji


# Create a Polars DataFrame from the list of dictionaries
kanjis = pl.DataFrame(new_data).select(
    pl.col(["character", "meanings","readings_on","wk_meanings", "wk_radicals"])
    )

print("Total number of kanjis in the df: ",kanjis.select(pl.count("character")))


words_tsv = r"C:\Users\dakot\OneDrive\Desktop\Git repositories\Kanji-Analysis\words.tsv"
words = pl.read_csv(words_tsv, separator="\t")


char_search = kanjis.item(80,"character")
print(
    f"Words with the kanji {char_search} in them:\n",
    words
    .filter(
        pl.col("word or phrase")
        .str.contains( char_search )
        )
    )







# Note: Some of the meanings and readings that were extracted from WaniKani have a ^ or a ! prefix.
# I added these to denote when an item is not a primary answer (^) or not an accepted answer (!) on WaniKani. 




def kanji_search(word_search):
    word_search = word_search.lower().capitalize()
    print(word_search,": ")
    df = kanjis.filter(
        pl.col("meanings").list.contains(word_search)

        &

        (  
            pl.col("wk_meanings").list.contains(word_search)
            |
            pl.col("wk_meanings").list.contains(f"^{word_search}") # easier then changing the dataframe
        )
    )
    return df
    

search_word = input("Insert word to search the kanji/s of: ")
search_df = kanji_search(search_word)
print(search_df)
