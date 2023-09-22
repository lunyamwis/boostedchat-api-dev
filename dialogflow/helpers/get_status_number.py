import re

pattern = r"`([^`]+)`"


def get_status_number(val):
    list_of_values = re.findall(pattern=pattern, string=val)
    return int(list_of_values[0])
