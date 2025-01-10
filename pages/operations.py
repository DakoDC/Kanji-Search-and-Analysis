
############## Operations on the saved kanjis library ###############


import streamlit as st
import polars as pl

# configures the streamlit page layout
st.set_page_config(layout="wide") 

st.write("# Operations on the saved kanjis")
st.write("Here you can search for specific features of the kanjis saved in the library")


# file with the saved kanjis library
saved_url = r"C:\Users\dakot\OneDrive\Desktop\Git-repositories\Kanji-Analysis\saved.tsv"

# reads the kanjis library file
saved = pl.read_csv(saved_url, separator='\t',truncate_ragged_lines=True).drop(pl.col(["save","jlpt_old"]))





######## Create filtered dataframes depending on the values of a slider ########


# Dataframes with the min and max values of the respective columns
mins  = saved.select(pl.col(["strokes","grade","freq","jlpt_new","wk_level"]).min().cast(pl.Int32))
maxes = saved.select(pl.col(["strokes","grade","freq","jlpt_new","wk_level"]).max().cast(pl.Int32))    

min_max = pl.concat([mins,maxes])


# Assigns each min/max to a variable
grade_min_0 = min_max["grade"][0]
grade_max_0 = min_max["grade"][1]
freq_min_0 = min_max["freq"][0]
freq_max_0 = min_max["freq"][1]
strokes_min_0 = min_max["strokes"][0]
strokes_max_0 = min_max["strokes"][1]
jlpt_min_0 = min_max["jlpt_new"][0]
jlpt_max_0 = min_max["jlpt_new"][1]


# Adds the sliders to the sidebar
with st.sidebar:
    st.header("Dataframe Filter Options")
    st.write("Move the sliders to filter the kanjis")
    grade_min, grade_max = st.slider(
        "Grade",
        min_value=grade_min_0, max_value=grade_max_0, value=(grade_min_0, grade_max_0))
    
    freq_min, freq_max = st.slider(
        "Daily Usage Ranking",
        min_value=freq_min_0, max_value=freq_max_0, value=(freq_min_0, freq_max_0))
    
    strokes_min, strokes_max = st.slider(
        "Strokes",
        min_value=strokes_min_0, max_value=strokes_max_0, value=(strokes_min_0, strokes_max_0))
    
    jlpt_min, jlpt_max = st.slider(
        "JLPT Level",
        min_value=jlpt_min_0, max_value=jlpt_max_0, value=(jlpt_min_0, jlpt_max_0))

# filter the saved kanjis df with the specified filters made with the sliders by the user
saved_filtered = saved.filter(
    (pl.col("grade") >= grade_min) & (pl.col("grade") <= grade_max),
    (pl.col("freq") >= freq_min) & (pl.col("freq") <= freq_max),
    (pl.col("strokes") >= strokes_min) & (pl.col("strokes") <= strokes_max),
    (pl.col("jlpt_new") >= jlpt_min) & (pl.col("jlpt_new") <= jlpt_max)

)

# Show the filtered dataframe
st.write("##### Saved kanjis library:",saved_filtered)



######## Search for kanjis in the filtered df with the specified radical ########


# gets the saved kanjis with the same radical
search_radical = st.text_input("Search for saved kanjis with the specified radical:").lower().capitalize()

# shows all saved kanjis with the chosen radical
saved_radicals = saved_filtered.filter(pl.col("wk_radicals").str.contains(search_radical))
if(search_radical):
    st.write(saved_radicals)




