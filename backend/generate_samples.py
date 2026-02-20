import pandas as pd
import numpy as np

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
    "Gen": [500, 505, 510], # Could be power or steam, LLM needs to look at values (500 MW is likely power, but no units here makes it hard)
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
# We can simulate duplicate headers by renaming columns after creation if we wanted, 
# but pandas will make them Temp and Temp.1 when reading anyway.
# To actually write duplicate headers to excel:
df_messy_2.columns = ["Power (MW)", "Temp", "Temp", "Steam Flow (TPH)", "H2O Usage", "Eff"]

df_messy_2.to_excel("sample_messy_2.xlsx", index=False)

print("Sample Excel files created successfully!")
