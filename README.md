# Kanji-Search-and-Analysis

The project consist in a Streamlit app where you can:
- Search and Save kanjis in a personal library.
- Make operations of analysis and filtering on the saved kanjis.
- Look at analysis of the kanjis and their correlations between eachother.


Disclaimer:  
The analysis are strictly dependent on the data an their respective sources, which might not be perfectly accurate:
- [kanji.json](https://github.com/davidluzgouveia/kanji-data)
- [words.tsv](https://www.kaggle.com/datasets/dinislamgaraev/popular-japanese-words)


# Index:  
- [Run the application](#run-the-application)  
- [Search and Save](#search-and-save)  
- [Operations](#operations)  
- [Graphical Analysis](#graphical-analysis)  


# Run the application
The project uses [uv](https://docs.astral.sh/uv/) for handling the libreries dependencies.  

To run the application go to the command line and enter in the folder of the analysis "Kanji-analysis" (use: cd *folder_path*).  
Then use the following command to start the application:  
- uv run streamlit run Search.py

# Search and Save
The app allows the user to search for a Kanji based on either its english translation or its Rōmaji prononciation (spelling in the roman alphabet).  
For example, the kanji "犬" can be searched both from writing "Dog", or "Inu" (romaji of the hiragana "いぬ")  

These kanjis can then be saved with the respective checkbox to a personal library, which persists even after exiting the app.  

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Search_page.png">  


# Operations
Here it's possible to make filtering operation on the saved kanjis, thanks to mutlple sliders on the sidebar.  
For example selecting only kanjis of a specified JLPT level or those written within 2 to 5 strokes, ...    


<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Operations_page.png">  

# Graphical Analysis
(There may be some initial lag due to the graph loading, changing page and re-entering the "Plots" page might help the first time it is opened)

This page shows a graphical analysis of the kanjis dataset, plus an interactiv network of the relations between kanjis and their radicals.  

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Plots_heatmap.png">  

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Kanji-Radicals_network.png">  



