import pandas as pd


def retrieve_json(filename):
    jsons = []
    xl = pd.ExcelFile(filename)
    for name in xl.sheet_names:
        df = pd.read_excel(filename, sheet_name=name)
        jsons.append(df.to_json(orient="records"))
    return jsons
