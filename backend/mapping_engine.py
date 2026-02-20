import json
import pandas as pd
import numpy as np
import re
from google import genai
from pydantic import TypeAdapter
from models import MappingResponse, APIResponse, ParsedData, UnmappedColumn
from dotenv import load_dotenv

import os

load_dotenv()

# Try to load canonical registry from multiple possible paths
canonical_registry_paths = [
    "backend/canonical_registry.json",
    "canonical_registry.json",
    "/app/backend/canonical_registry.json",
    "/app/canonical_registry.json"
]
CANONICAL_REGISTRY = None
for path in canonical_registry_paths:
    if os.path.exists(path):
        with open(path, "r") as f:
            CANONICAL_REGISTRY = json.load(f)
        break
if CANONICAL_REGISTRY is None:
    raise FileNotFoundError("Could not find canonical_registry.json in any expected location")

def clean_numeric_value(val: any) -> float | None:
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val_str = val.strip().lower()
        if val_str in ['yes', 'true', 'on']:
            return 1.0
        if val_str in ['no', 'false', 'off', 'n/a', 'nan', 'null', 'none', '']:
            return None
        # Remove commas, percents, currency, etc.
        cleaned = re.sub(r'[^\d\.-]', '', val_str)
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None

def process_excel_file(file_path: str) -> dict:
    # 1. Read raw to find header
    # Determine file type and use appropriate engine
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext in ['.xlsx', '.xlsm']:
            # Modern Excel format - use openpyxl
            df_raw = pd.read_excel(file_path, engine="openpyxl", header=None)
        elif file_ext == '.xls':
            # Legacy Excel format - use xlrd
            df_raw = pd.read_excel(file_path, engine="xlrd", header=None)
        elif file_ext == '.csv':
            # CSV file
            try:
                df_raw = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', header=None)
            except UnicodeDecodeError:
                df_raw = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip', header=None)
        else:
            # Try openpyxl first for unknown extensions
            try:
                df_raw = pd.read_excel(file_path, engine="openpyxl", header=None)
            except Exception:
                try:
                    df_raw = pd.read_excel(file_path, engine="xlrd", header=None)
                except Exception:
                    try:
                        df_raw = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', header=None)
                    except UnicodeDecodeError:
                        df_raw = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip', header=None)
    except Exception as e:
        raise Exception(f"Failed to read file {file_path}: {str(e)}")

    # Find header row
    header_row_idx = 0
    max_score = -1
    for idx, row in df_raw.head(20).iterrows():
        score = row.dropna().apply(lambda x: isinstance(x, str)).sum()
        if score > max_score:
            max_score = score
            header_row_idx = idx

    warnings = []
    if header_row_idx > 0:
        warnings.append(f"Skipped {header_row_idx} title/metadata rows to find headers.")

    # Re-read with correct header
    try:
        if file_ext in ['.xlsx', '.xlsm']:
            df = pd.read_excel(file_path, engine="openpyxl", header=header_row_idx)
        elif file_ext == '.xls':
            df = pd.read_excel(file_path, engine="xlrd", header=header_row_idx)
        elif file_ext == '.csv':
            try:
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', header=header_row_idx)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip', header=header_row_idx)
        else:
            # Try openpyxl first for unknown extensions
            try:
                df = pd.read_excel(file_path, engine="openpyxl", header=header_row_idx)
            except Exception:
                df = pd.read_excel(file_path, engine="xlrd", header=header_row_idx)
    except Exception as e:
        raise Exception(f"Failed to read file with header at row {header_row_idx}: {str(e)}")

    # Ensure unique headers
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    headers = df.columns.astype(str).tolist()
    
    # 2. Call LLM to map headers
    sample_data = df.head(3).to_dict(orient="records")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = f"""You are the LatSpace Data Mapping Agent. Your task is to map 'Messy Headers' from a factory Excel sheet to a 'Canonical Parameter Registry'.

Rules:
1. Strict Mapping: Only map a header if it clearly matches a parameter in the registry. If no match, return a mapped_parameter of "Unknown".
2. Contextual Clues: Look at the unit or sample data to decide between parameters (e.g., 'power_generation' or 'steam_generation').
3. Asset Extraction: If the header is 'Boiler 1 - Temp', extract 'Boiler 1' as the Asset and 'temperature' as the Parameter.

Return EXACTLY and ONLY a JSON object with a single key "mappings", containing a list of objects with the specified requirements.
Example Output Format:
{{
  "mappings": [
    {{
      "original_header": "Gen",
      "mapped_parameter": "power_generation",
      "confidence": 0.95,
      "detected_asset": null
    }}
  ]
}}

Canonical Registry:
{json.dumps(CANONICAL_REGISTRY, indent=2)}

Messy Headers to Map:
{json.dumps(headers, indent=2)}

Sample Data (first 3 rows for context):
{json.dumps(sample_data, indent=2)}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
    )
    
    mapping_data = TypeAdapter(MappingResponse).validate_json(response.text)
    mappings = mapping_data.model_dump()["mappings"]
    
    # Create lookup dictionary
    header_mapping = {m["original_header"]: m for m in mappings}
    
    # 3. Assemble full cell data
    parsed_data = []
    unmapped_columns = []
    
    # Identify unmapped upfront
    for col_idx, header in enumerate(headers):
        match = header_mapping.get(header)
        if not match or match["mapped_parameter"] == "Unknown":
            unmapped_columns.append({
                "col": col_idx,
                "header": header,
                "reason": "No matching parameter found in canonical registry"
            })
    
    # Iterate rows and cells
    for row_idx, row in df.iterrows():
        # Skip completely empty rows
        if row.isna().all():
            continue
            
        real_row = header_row_idx + 2 + row_idx # +2 because header is 1-indexed, and data is 1 after that
        
        for col_idx, header in enumerate(headers):
            match = header_mapping.get(header)
            if not match or match["mapped_parameter"] == "Unknown":
                continue
                
            raw_val = row[header]
            if pd.isna(raw_val) or (isinstance(raw_val, str) and raw_val.strip() == ''):
                continue
                
            parsed_val = clean_numeric_value(raw_val)
            
            # Map float confidence to string for API requirement
            conf_score = match["confidence"]
            if conf_score >= 0.8:
                conf_str = "high"
            elif conf_score >= 0.5:
                conf_str = "medium"
            else:
                conf_str = "low"
            
            parsed_data.append({
                "row": int(real_row),
                "col": col_idx,
                "param_name": match["mapped_parameter"],
                "asset_name": match["detected_asset"],
                "raw_value": str(raw_val),
                "parsed_value": parsed_val,
                "confidence": conf_str
            })

    # 4. Final constructed API Response
    api_response = {
        "status": "success",
        "header_row": header_row_idx + 1, # 1-indexed
        "parsed_data": parsed_data,
        "unmapped_columns": unmapped_columns,
        "warnings": warnings
    }
    
    # Validate structure and return dict
    validated = TypeAdapter(APIResponse).validate_python(api_response)
    return validated.model_dump()
