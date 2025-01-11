
######## Operations on the saved kanjis library ###########

import streamlit as st
import polars as pl

# configures the streamlit page layout
st.set_page_config(layout="wide") 


st.write("# Operations on the saved kanjis")
st.write("Here you can search for specific features of the kanjis saved in the library")



# file with the saved kanjis library
saved_url = r"saved.tsv"

# reads the kanjis library file
saved = pl.read_csv(saved_url, separator='\t',truncate_ragged_lines=True).drop(pl.col(["save","jlpt_old"]))

# Case with no kanjis saved yet
if saved.is_empty():
    st.info('''There aren't any save kanjs  
            Save some kanjis from the "Search" page to be able to make operations on them''')
    st.stop()




######## Create filtered dataframes depending on the values of a slider ########


# Assigns each min/max value to a variable
grade_min_0 = 1
grade_max_0 = 10
freq_min_0 = 1
freq_max_0 = 2500
strokes_min_0 = 1
strokes_max_0 = 24
jlpt_min_0 = 1
jlpt_max_0 = 5


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
    
    st.info("Some kanjis might not have all the fields of the sliders")
    remove_null = st.checkbox("Remove kanjis with missing data")


# filter the saved kanjis df with the specified filters made with the sliders by the user

if remove_null:
    saved_filtered = saved.filter(
        (pl.col("grade") >= grade_min) & (pl.col("grade") <= grade_max),
        (pl.col("freq") >= freq_min) & (pl.col("freq") <= freq_max),
        (pl.col("strokes") >= strokes_min) & (pl.col("strokes") <= strokes_max),
        (pl.col("jlpt_new") >= jlpt_min) & (pl.col("jlpt_new") <= jlpt_max)
    )
else:
    saved_filtered = saved.filter(
            (pl.col("grade") >= grade_min) & (pl.col("grade") <= grade_max),
            (pl.col("freq") >= freq_min) & (pl.col("freq") <= freq_max),
            (pl.col("strokes") >= strokes_min) & (pl.col("strokes") <= strokes_max),
            (pl.col("jlpt_new") >= jlpt_min) & (pl.col("jlpt_new") <= jlpt_max)
        ).vstack( # add the kanjis that are missing the grade, freq and jlpt_new fields
            saved.filter(pl.col("freq").is_null()).filter(
                (pl.col("strokes") >= strokes_min) & (pl.col("strokes") <= strokes_max), # check only for the strokes
            )
        ).vstack( # add the kanjis that are missing the strokes, grade, freq and jlpt_new fields
            saved.filter(pl.col("freq").is_null()).filter(
                (pl.col("jlpt_new") >= jlpt_min) & (pl.col("jlpt_new") <= jlpt_max), # check only for the strokes
            )
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




