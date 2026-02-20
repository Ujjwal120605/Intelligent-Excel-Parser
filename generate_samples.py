import pandas as pd

# 1. Clean File - Perfect match to canonical registry
clean_data = {
    "power_generation": [500, 505, 510],
    "coal_consumption": [200, 202, 205],
    "temperature": [85.5, 86.0, 85.8],
    "steam_generation": [1500, 1510, 1505],
    "pressure": [12.5, 12.6, 12.4]
}
df_clean = pd.DataFrame(clean_data)
df_clean.to_excel("sample_clean.xlsx", index=False)

# 2. Messy File 1 - Ambiguous names, missing units
messy_data_1 = {
    "Gen": [500, 505, 510], # Could be power or steam
    "Coal (MT)": [200, 202, 205],
    "Boiler 1 - Temp": [85.5, 86.0, 85.8],
    "Press": [12.5, 12.6, 12.4],
    "Random Column": ["A", "B", "C"] # Should be mapped to Unknown
}
df_messy_1 = pd.DataFrame(messy_data_1)
df_messy_1.to_excel("sample_messy_1.xlsx", index=False)

# 3. Messy File 2 - Duplicate headers and complex names
messy_data_2 = {
    "Power (MW)": [500, 505, 510],
    "Boiler Temp": [85.5, 86.0, 85.8],
    "Turbine Temp": [120.5, 121.0, 120.8], # Duplicate concept 'temperature', different assets
    "Steam Flow (TPH)": [1500, 1510, 1505],
    "H2O Usage": [1000, 1005, 1010], # Tricky name for water_consumption
    "Eff": [95.5, 96.0, 95.8]
}

df_messy_2 = pd.DataFrame(messy_data_2)

# To actually write duplicate headers to excel:
df_messy_2.columns = ["Power (MW)", "Temp", "Temp", "Steam Flow (TPH)", "H2O Usage", "Eff"]

df_messy_2.to_excel("sample_messy_2.xlsx", index=False)

# 4. EXTREME Mess - Missing headers, random strings, bad indexing, merged-like data
import numpy as np
extreme_mess_data = {
    # Unnamed column that pandas will parse as Unnamed: 0
    "Unnamed: 0": ["Row 1", "Row 2", "Row 3", "Row 4", "Row 5"],
    
    # Completely ambiguous title, but data clearly looks like power (MW)
    "Elec": [500, None, 510, 505, "ERROR_READING"], 
    
    # Has asset embedded in the header but data is messy
    "Boiler 2 Pressure": [12.5, "12.6 bar", 12.4, None, 13.0], 
    
    # Duplicate concept, but terrible name
    "Hotness": [np.nan, 86.0, 85.8, "High", 85.9], 
    
    # Random text column that should not map to anything
    "Operator Notes": ["Shift change", "All good", "Checked valve", "Lunch break", ""],
    
    # Missing explicit unit, but data looks like efficiency %
    "Performance": [0.95, 0.96, 0.94, None, 0.95],
    
    # Another duplicate concept with different asset
    "Cooling Tower Temp": [30.1, 30.5, 30.2, 31.0, 30.4]
}

df_extreme = pd.DataFrame(extreme_mess_data)

# Add a completely empty row in the middle to simulate bad indexing
df_extreme.loc[2.5] = [None, None, None, None, None, None, None]
df_extreme = df_extreme.sort_index().reset_index(drop=True)

df_extreme.to_excel("sample_extreme_mess.xlsx", index=False)

print("Sample Excel files created successfully!")
