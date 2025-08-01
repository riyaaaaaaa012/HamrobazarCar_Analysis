# HamrobazarCar_Analysis 

**Analysis of car listings from HamroBazar**, including data cleaning, exploration, and condition-based visualizations.

##  Overview

This repository contains an analysis of car listing data from HamroBazar, with goals to:

- Clean and standardize listing conditions (`Brand New`, `Like New`, `Used`)  
- Explore frequency and distribution of conditions  
- Visualize condition breakdown through charts (e.g. pie chart)  

---

##  Setup and Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/riyaaaaaaa012/HamrobazarCar_Analysis.git
   cd HamrobazarCar_Analysis
   ```

2. **Create and activate a Python virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # macOS/Linux
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

##  Data Scraping and Analysis

1. **Run `data_scrapper.py`**  
   ```bash
   python data_scrapper.py
   ```
   - Scrapes car listings from HamroBazar.
   - Generates two raw data files containing extracted car data.

2. **Run `data_cleaning.ipynb`**  
   - Cleans the scraped raw data.
   - Fixes inconsistencies (e.g., condition field), removes noise and duplicates.
   - Saves the cleaned dataset into a new CSV file.

3. **Run `analysis.ipynb`**  
   - Performs data exploration and visualization.
   - Displays charts and graphs showing:
     - Distribution of car conditions
     - Price ranges
     - Listings per brand and more








