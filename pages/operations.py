
############## Operations on the saved kanjis library ###############


import streamlit as st
import polars as pl

# file with the saved kanjis library
saved_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\saved.tsv"

# reads the kanjis library file
saved = pl.read_csv(saved_url, separator='\t',truncate_ragged_lines=True)

# gets the saved kanjis with the same radical
search_radical = st.text_input("Search for saved kanjis with the same radical:").lower().capitalize()

# shows all saved kanjis with the chosen radical
saved_radicals = saved.filter(pl.col("wk_radicals").str.contains(search_radical))
if(search_radical):
    st.write(saved_radicals)










