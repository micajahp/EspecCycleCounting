import scipy
import os
import time
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from colorama import Fore, init  # For fancy prints to console

init(autoreset=True)

# datetime.strptime() For Formatting
nowish = time.time()
Deviation = 10

# data points allowed to skip before logging any points
resolution = 30


def ListFiles(FilePath="./"):

    FileList = []
    if FilePath[-1] != "/" and FilePath[-1] != "\\":
        q = 0
        p = 0
        for i in enumerate(FilePath):
            if "\\" in i:
                p = q
                print(f"{i}\n")
                print(f"{p}\n")
            q += 1
        print(FilePath[0: p + 1])
        FilePath = FilePath[0: p + 1]
    ListOfFiles = os.listdir(FilePath)
    for items in ListOfFiles:
        if ".csv" in items or ".xlsx" in items or ".xls" in items:
            FileList.append(FilePath + items)
    return FileList


def LoadColumns(FileList):

    with open(FileList, "r") as r:
        Legend = r.readline()
        Legend = Legend.replace("\n", "")
        Legend = Legend.split(",")
    Axis_List = {}
    Axis_List.clear()
    try:
        Axis_List = {"timeStamp": Legend.index("datetime")}
    except Exception as e:
        print(e)
        # Timestamp does not exist, use Date
        Axis_List = {"Date": Legend.index("Date")}
    ##########################################################################
    # All Relevant Options for Chamber Log output Listed
    for i in Legend:
        if "program_step" in i:
            Axis_List["program_step"] = Legend.index("program_step")
        if "program_key" in i:
            Axis_List["program_key"] = Legend.index("program_key")
        if "temp__set_value" in i:
            Axis_List["temp__set_value"] = Legend.index("temp__set_value")
        if "Temp Setpoint" in i:
            Axis_List["temp__set_value"] = Legend.index("Temp Setpoint °C")
        if "Temp PV" in i:
            Axis_List["temp__process_value"] = Legend.index("Temp PV °C")
        if "temp__process_value" in i:
            ww = "temp__process_value"
            Axis_List[ww] = Legend.index("temp__process_value")
        if "temp__air_set_value" in i:
            ww = "temp__air_set_value"
            Axis_List[ww] = Legend.index("temp__air_set_value")
        if "temp__product_set_value" in i:
            Axis_List["temp__product_set_value"] = Legend.index(
                "temp__product_set_value"
            )
        if "temp__air_process_value" in i:
            Axis_List["temp__air_process_value"] = Legend.index(
                "temp__air_process_value"
            )
        if "temp__product_process_value" in i:
            Axis_List["temp__product_process_value"] = Legend.index(
                "temp__product_process_value"
            )
    return Axis_List


CSV_List = ListFiles()
FileNumber = 0
for items in CSV_List:
    SetTag = ""
    ProcessTag = ""
    ProdTag = ""
    try:
        if "Axis_Dict" not in dir():
            Axis_Dict = dict()
        Axis_Dict.clear()
    except Exception as e:
        print(e)

    Axis_Dict = LoadColumns(CSV_List[FileNumber])
    print("This log contains columns for")
    Yaxis = dict()
    Xaxis = []
    for i in Axis_Dict:
        print(f"{Fore.GREEN}{i}", end=" ")
        print(f"in column {Fore.YELLOW}{Axis_Dict[i]}")
        Yaxis[i] = []

    if True:
        with open(CSV_List[FileNumber], "r") as r:
            inc = 1
            datadata = r.readline()
            while datadata:
                data = []
                datadata = r.readline()
                if datadata == "":
                    break
                datadata = datadata.replace("\n", "")
                datadata = datadata.split(",")

                for i in Axis_Dict:
                    if "product" in i:
                        ProdTag = True
                    if "timeStamp" not in i and "Date" not in i:
                        if "Time" not in i:
                            if "value" in i:
                                try:
                                    Yaxis[i] += [float(datadata[Axis_Dict[i]])]
                                except Exception as e:
                                    print(e)
                                    Yaxis[i] += [datadata[Axis_Dict[i]]]
                        else:
                            Yaxis[i] += [datadata[Axis_Dict[i]]]
                    if "timeStamp" in i:
                        Xaxis.append(datadata[Axis_Dict["timeStamp"]])
                    if i == "Date":
                        Xaxis.append(inc)
                inc += 1
        length_of_file = inc

    fig1 = go.Figure()
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    temp = 0
    Step_Cycles = 0
    inc = 0
    for i in Axis_Dict:
        if ("product_set" in i or "Temp Setpoint" in i) and SetTag == "":
            SetTag = i
        if ("product_process" in i or "Temp PV" in i) and ProcessTag == "":
            ProcessTag = i
        else:
            if ("set" in i or "Temp Setpoint" in i) and SetTag == "":
                SetTag = i
            if ("process" in i or "Temp PV" in i) and ProcessTag == "":
                ProcessTag = i
        if "value" in i:
            fig1["layout"]["yaxis"].update(autorange=True)
    ##########################################################################
    try:  # Counts cycles By program steps
        X_Scatter = []
        Y_Scatter = []

        for i in Yaxis["program_step"]:
            if i != "":
                if temp > int(i):
                    Step_Cycles += 1

                temp = int(i)
            elif i == "":
                temp = 0
            X_Scatter.append(Xaxis[inc])
            Y_Scatter.append(Step_Cycles)

            inc += 1

        elapsed = time.time() - nowish
        print(f"Loaded {Fore.CYAN}{length_of_file} ", end="")
        print(f"lines in {Fore.RED}{elapsed} {Fore.WHITE}Seconds")
        fig1.add_trace(
            go.Scatter(
                x=X_Scatter,
                y=Y_Scatter,
                name=f"<b>{Step_Cycles}</b> By Completed Program Steps",
                mode="lines",
                line={"width": 32, "shape": "spline"},
            ),
            secondary_y=True,
        )
        print(f"{Step_Cycles}:{Fore.MAGENTA} By counting program Steps")
    except Exception as e:
        print(e)
        print("No Steps in Log")
    ##########################################################################
    # Counts Steps by peak function
    Peaky = {"Peaks": []}
    minusPeaky = {"Peaks": []}
    peakx = []
    minuspeakx = []

    for i in Axis_Dict:
        if "process" in i or "Temp PV" in i:
            # Yaxis process key, prominence, distance between points should be
            #                            minimum 75% of cycle time in sec /10
            #                              Value should be minutes*6
            peaks, properties = scipy.signal.find_peaks(
                Yaxis[i], prominence=60, distance=80
            )
            minuspeaks, properties = scipy.signal.find_peaks(
                np.negative(Yaxis[i]), prominence=60, distance=80
            )

            for p in peaks:
                if Yaxis[i][p] > Yaxis[f"{SetTag}"][p] - Deviation:
                    Peaky["Peaks"] += [Yaxis[i][p]]
                    peakx.append(Xaxis[p])

            for p in minuspeaks:
                if Yaxis[i][p] < Yaxis[f"{SetTag}"][p] + Deviation:
                    minusPeaky["Peaks"] += [Yaxis[i][p]]
                    minuspeakx.append(Xaxis[p])

    peakgraph = []
    xpeakgraph = []
    rang = 0
    inc = 0
    dataloss = 0
    for i in Xaxis:

        if rang in peaks:
            peakgraph.append(Yaxis[f"{ProcessTag}"][rang])
            xpeakgraph.append(i)
            dataloss = 0
        elif rang in minuspeaks:
            peakgraph.append(Yaxis[f"{ProcessTag}"][rang])
            xpeakgraph.append(i)
            dataloss = 0
        else:
            dataloss += 1
        if dataloss >= resolution:
            peakgraph.append(Yaxis[f"{ProcessTag}"][rang])
            xpeakgraph.append(i)
            dataloss = 0

        rang += 1

    XTrendPeak = []
    YTrendPeak = []
    inc = 0
    rang = 0
    for i in Xaxis:
        XTrendPeak.append(i)
        rang += 1
        if rang in peaks:
            inc += 1
        YTrendPeak.append(inc)
    # Draw Peak TrendLine
    fig1.add_trace(
        go.Scatter(
            x=XTrendPeak,
            y=YTrendPeak,
            mode="lines",
            name=f"Reached High Set Point <b>{max(YTrendPeak)}</b> Times",
        ),
        secondary_y=True,
    )
    print(f"{max(YTrendPeak)}:{Fore.RED} By Reaching High Setpoints")
    # Draw Peaks of process value
    fig1.add_trace(
        go.Scatter(
            x=xpeakgraph,
            y=peakgraph,
            name="Limited Resolution Process Value",
            mode="lines",
        ),
        secondary_y=False,
    )

    XTrendPeak = []
    YTrendPeak = []
    inc = 0
    rang = 0
    for i in Xaxis:
        XTrendPeak.append(i)
        rang += 1
        if rang in minuspeaks:
            inc += 1
        YTrendPeak.append(inc)
    # Draw -Peak TrendLine
    fig1.add_trace(
        go.Scatter(
            x=XTrendPeak,
            y=YTrendPeak,
            name=f"Reached Low Set Point <b>{max(YTrendPeak)}</b> Times",
        ),
        secondary_y=True,
    )
    print(f"{max(YTrendPeak)}:{Fore.CYAN} By Reaching Low Setpoints")
    # Draw Low Peaks
    ##########################################################################
    fig1["layout"]["yaxis"].update(autorange=True)

    fig1.update_yaxes(
        title_text="<b>Chamber Set Points</b>",
        secondary_y=False)
    fig1.update_yaxes(title_text="<b>Total Cycles</b>", secondary_y=True)
    fig1.update_traces(line={"width": 1})
    fig1.update_layout(title="Total Cycles")
    fig1.write_html(f"{items[0:3]}fig{FileNumber}.html")
    fig1.show()
    print("\n\n")
    FileNumber += 1
