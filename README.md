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

If you don't already have uv installed, as instructed on the [uv website](https://docs.astral.sh/uv/) on the section "Introduction", go to the command line and type:  
For windows:
- `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

For macOS or linux:
- `curl -LsSf https\://astral.sh/uv/install.sh | sh`  

It might be necessary to reboot the pc for the changes to apply.  

After downloading the project files,  
go in the command line and type the following, by replacing *folder_path* with the path of the folder just dowloaded:
- `cd folder_path`

Then use the following command to start the application:  
- `uv run streamlit run Search.py`

This will download the needed python libraries for the application and run it on your browser, the first time it might take some time to load.  

# Search and Save
The app allows the user to search for a Kanji based on either its english translation or its Rōmaji prononciation (spelling in the roman alphabet).  
For example, the kanji "犬" can be searched both from writing "Dog", or "Inu" (romaji of the hiragana "いぬ")  

These kanjis can then be saved with the respective checkbox to a personal library, which persists even after exiting the app.  

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Search_page.png">  


# Operations
Here it's possible to make filtering operation on the saved kanjis, thanks to mutlple sliders on the sidebar.  
For example selecting only kanjis of a specified JLPT level or those written within 2 to 5 strokes, ...    
(Some kanjis/phrases might have missing data in the sliders' fields, It is given the option to show or not these entries in the list)

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Operations_page.png">  

# Graphical Analysis
(There may be some initial lag due to the graph loading, changing page and re-entering the "Plots" page might help the first time it is opened)

This page shows a graphical analysis of the kanjis dataset, plus an interactiv network of the relations between kanjis and their radicals.  

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Plots_heatmap.png">  

<img src="https://github.com/DakoDC/Kanji-Search-and-Analysis/blob/main/Preview_images/Kanji-Radicals_network.png">  



