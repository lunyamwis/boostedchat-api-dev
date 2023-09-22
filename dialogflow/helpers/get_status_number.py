import re

# pattern = r"`([^`]+)`"
pattern = r"\d+"


def get_status_number(val):
    list_of_values = re.findall(pattern=pattern, string=val)
    print(list_of_values)
    return int(list_of_values[0])
