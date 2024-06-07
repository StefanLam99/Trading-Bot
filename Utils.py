import pandas as pd
import numpy as np
import os


def obtain_period_data(df, first_date, last_date):
    return df[first_date:last_date]


def classify(current, future):
    if float(future) > float(current):  # if the future price is higher than the current, that's a buy, or a 1
        return 1
    else:  # otherwise... it's a 0!
        return 0


def check_save_location(path: str):
    if ~os.path.exists(path):
        os.makedirs('/'.join(path.split('/')[0:-1]), exist_ok=True)


def convert_time_to_str(time, format="%Y-%m-%d %H:%M"):
    """
    :param time: float in seconds from the time() module
    :param format: format of the time
    :return:
    """
    return pd.to_datetime(time, unit="s").strftime(format)

