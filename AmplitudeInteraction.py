import pandas as pd
import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
iValues = {"daily" : '1', "weekly" : '7', "monthly" : '30', "hourly" : '-3600000', "realtime" : '-300000'}
measures = {'uniques' : 'uniques', 'event totals' : 'totals', 'active %' : 'pct_dau', 'average' : 'average'}
keyFile = open(r'./.secret/api_keys.txt','r')
keys = keyFile.read().split('\n')
def getErrorPlots(inputJsonFileName):
    with open(inputJsonFileName) as f:
        inputJson = json.load(f)
    plotName = inputJsonFileName[:-5] + 'plot.png'
    chartType = inputJson['body']['chart_type']
    errors = inputJson['body']['events']
    dfList = []
    interval = iValues[inputJson['body']['interval']]
    metric = measures[inputJson['body']['measures']]
    endDate = str(datetime.now().date()).replace('-','')
    if (interval == '-3600000' or interval == '-300000'):
        startDate = endDate
    else:
        endVal = inputJson['body']['interval_range'][-1]
        if (endVal == 'd'):
            startDate = str((datetime.now() + timedelta(-int(inputJson['body']['interval_range'][:-1]) + 1)).date()).replace('-','')
        elif (endVal == 'w'):
            startDate = str((datetime.now() + timedelta(-(int(inputJson['body']['interval_range'][:-1]) * 7) + 1)).date()).replace('-','')
        elif (endVal == 'm'):
            startDate = str((datetime.now() + timedelta(-(int(inputJson['body']['interval_range'][:-1]) * 30) + 1)).date()).replace('-','')
        else:
            startDate = endDate

    for i in range(len(errors)):
        HTTPString = ('https://amplitude.com/api/2/events/segmentation?e=' + str(errors[i]) + '&start=' + startDate + '&end=' + endDate + '&i=' + interval + '&m=' + metric).replace("'", '"')
        response = requests.get(HTTPString, auth = HTTPBasicAuth(keys[0], keys[1]))
        if str(response) != '<Response [200]>':
            return 'API call Failed'
        response_json = response.json()
        tempDF = pd.DataFrame(response_json['data']['series'], columns = response_json['data']['xValues']).transpose()
        if not (tempDF.empty):
            if (response_json['data']['seriesLabels'] != [0]):
                tempDF.columns = [el[1] for el in response_json['data']['seriesLabels']]
            if interval in ['1','7']:
                tempDF = tempDF.rename(index = lambda x: x.split('T')[0])
            else:
                tempDF = tempDF.rename(index = lambda x: x.split('T')[1])
            if not (str(tempDF.columns[0]).isdigit()):
                tempDF = tempDF.rename(columns = lambda x: errors[i]['event_type'] + ', ' + x)
            else:
                tempDF = tempDF.rename(columns = lambda x: errors[i]['event_type'])
            dfList.append(tempDF)

    df = pd.DataFrame()
    for i in dfList:
        if df.empty:
            df = i
        else:
            df = df.join(i)

    fig, ax = plt.subplots()
    plt.rcParams['font.size'] = '8'
    sns.set_style('whitegrid')
    if chartType in ['bar', 'line']:
        if chartType == 'line':
            ax = df.plot(kind='line', marker='o')
        else:
            ax = df.plot(kind='bar', width=0.75)
            rects = ax.patches
            autolabelbar(rects, ax, False)
    elif chartType == 'stacked bar':
        ax = df.plot.bar(stacked=True)
        rects = ax.patches
        autolabelbar(rects, ax, True)
    elif chartType == 'stacked area':
        ax = df.plot.area(alpha=0.5)
    ax.grid(alpha=0.2, b=True)
    ax.figure.autofmt_xdate()
    plt.xlabel('Dates')
    plt.ylabel(inputJson['body']['measures'].title())
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),
       fancybox=True, shadow=True, ncol=1)
    plt.savefig(plotName, dpi=300, bbox_inches='tight')
    return plotName

def autolabelbar(rects, ax, stacked=False):
    # Get y-axis height to calculate label position from.
    (y_bottom, y_top) = ax.get_ylim()
    y_height = y_top - y_bottom
    for rect in rects:
        height = rect.get_height()
        label_position = rect.get_y() + height / 2 if stacked else height + (y_height * 0.01)
        if height:
            t = ax.text(rect.get_x() + rect.get_width()/2., label_position,
                str(int(height)),
                ha='center', va='bottom', in_layout=True, alpha=0.7)
getErrorPlots('input.json')
