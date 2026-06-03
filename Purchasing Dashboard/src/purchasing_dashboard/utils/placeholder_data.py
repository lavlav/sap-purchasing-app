from collections.abc import Sequence
from typing import Any, Dict, Hashable
import pandas as pd

#This data populates the DataTable during loading to size it appropriately for the loading spinner.

def generate_placeholder_table_data(columns: list[str]) -> Sequence[Dict[Any, Any]]:
    columns = [col.replace(" ","") for col in columns]
    working = pd.DataFrame(columns=columns)
    #columns = ["VendorId", "VendorName", "ItemCode", "ItemName", "WorkingDaysOnHand", "OnOrder"]
    loremipsum = """LOREM IPSUM DOLOR SIT AMET CONSECTETUR ADIPISCING ELIT SED DO EIUSMOD""".split()
    j = 0
    for i in range(1,10):
        row = pd.DataFrame(columns=columns)
        for col in columns:
            row.at[i,col] = loremipsum[j % 10]
            j = j + 1
        working = pd.concat([working,row])
    result: Sequence[Dict[str, str]] = working.to_dict(orient="records") # type: ignore
    return result