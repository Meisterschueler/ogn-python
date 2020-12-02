import os
from flask import current_app

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, WheelZoomTool, PanTool, ResetTool
from bokeh.resources import CDN
from bokeh.embed import file_html

import pandas as pd
import numpy as np

COMMON_FREQUENCIES = [
    [84.015, 87.2250, 'BOS 4m'],
    [87.500, 108.0000, 'UKW Rundfunk'],
    [108.000, 111.9750, 'ILS'],
    [112.000, 117.9750, 'VOR'],
    [117.975, 137.0000, 'Flugfunk'],
    [143.000, 146.0000, 'Amateurfunk 2m'],
    [165.210, 173.9800, 'BOS 2m'],
    [177.500, 226.5000, 'DVB-T VHF'],
    [273.000, 312.0000, 'Militär'],
    [390.000, 399.9000, 'BOS Digital'],
    [430.000, 440.0000, 'Amateurfunk 70cm'],
    [448.600, 449.9625, 'BOS 70cm'],
    [474.000, 786.0000, 'DVB-T UHF'],
    [791.000, 821.0000, 'LTE downlink'],
    [832.000, 862.0000, 'LTE uplink'],
    [868.000, 868.6000, 'Flarm 868.3MHz'],
    [880.000, 915.0000, 'GSM 900 uplink'],
    [925.000, 960.0000, 'GSM 900 downlink'],
    [1025.000, 1095.0000, 'Funknavigation'],
    [1164.000, 1215.0000, 'Funknavigation (DME,TACAN)'],
    [1429.000, 1452.0000, 'Militär'],
]


def get_bokeh_frequency_scan(frequency_scan_file):
    # Read the frequency scan file
    df_scan = pd.read_csv(os.path.join(current_app.config['UPLOAD_PATH'], frequency_scan_file.name), header=None)
    df_scan.columns = ['date', 'time', 'hz_low', 'hz_high', 'hz_step', 'samples'] + [f"signal{c:02}" for c in range(1, len(df_scan.columns) - 5)]

    xval = df_scan['hz_low'] / 1000000
    yval = df_scan['signal01']

    # Read the common frequences
    df_freq = pd.DataFrame(COMMON_FREQUENCIES, columns=['hz_low', 'hz_high', 'description'], dtype=float)

    N = len(df_freq.index)
    low = df_freq['hz_low']
    high = df_freq['hz_high']

    x = high - (high - low) / 2.0
    y = 0 * np.ones(N)
    width = high - low
    height = 50 * np.ones(N)
    desc = df_freq['description']

    frequency_source = ColumnDataSource(data=dict(low=low, high=high, x=x, y=y, width=width, height=height, desc=desc))

    # Create the figure with tool tips
    fig = figure(plot_width=900, plot_height=500, title=f"Signalauswertung {frequency_scan_file.receiver.name}", tools=[PanTool(), WheelZoomTool(), ResetTool()])
    r1 = fig.rect(x='x', y='y', width='width', height='height', color="lightgrey", source=frequency_source, legend="Gängige Frequenzen")
    r2 = fig.line(xval, yval, legend=f"Messung (gain={frequency_scan_file.gain})")
    r3 = fig.line(x=[868.3, 868.3], y=[-25, 25], color="red", legend="Flarm")

    fig.add_tools(HoverTool(renderers=[r1], tooltips={"info": "@desc @low-@high MHz"}))
    fig.add_tools(HoverTool(renderers=[r2], tooltips={"f [MHz]": "$x", "P [dB]": "$y"}))

    fig.xaxis.axis_label = "Frequenz [MHz]"
    fig.yaxis.axis_label = "Signalstärke [dB]"
    fig.legend.click_policy = 'hide'

    return file_html(fig, CDN)
