import pandas as pd
import numpy as np


def obtain_period_data(df, first_date, last_date):
    return df[first_date:last_date]


def classify(current, future):
    if float(future) > float(current):  # if the future price is higher than the current, that's a buy, or a 1
        return 1
    else:  # otherwise... it's a 0!
        return 0
