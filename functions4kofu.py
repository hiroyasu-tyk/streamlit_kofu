'''
関数定義
'''
import requests
import io
import pandas as pd
import matplotlib     
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import subprocess
from datetime import datetime as dt, timedelta
import glob
import seaborn as sns

ble_src_dir = "./csv/ble/kofu/"
population_url = "https://8tops.yamanashi.ac.jp/kofu/bt/getPopulation_csv.php"
kofu_base_url = "https://8tops.yamanashi.ac.jp/kofu/"

'''
センサの名称などの取得
'''
def getSensorInfo(gr=1):
    sensors = pd.read_csv("./sensor_points.2021.csv",
                         dtype={"短縮名": str})
    sensors.set_index("センサ名", inplace=True)
    return sensors.to_dict(orient='index')

'''
引数：センサIDのリスト　返り値：名前のリスト
'''
def sensorNamesByIds(ids, gr=0):
    ret_list = []
    sensors = getSensorInfo(gr)
    for id in ids:
        if id in sensors:
            ret_list.append(sensors[id]['地点名'])
    return ret_list

def sensorNameById(id, gr=0):
    sensors = getSensorInfo(gr)
    return sensors[id]['地点名']

def sensorNameDictById(ids, gr=0):
    ret_dict = {}
    sensors = getSensorInfo(gr)
    for id in ids:
        ret_dict[id] = sensors[id]['地点名']
    return ret_dict

'''
DataFrameの列名をセンサ名から地点名に変更する
'''
def change_cols_name(df, gr=0):
        sensor_info = getSensorInfo(gr)
        new_cols = {}
        for id in df.columns.to_list():
            if id in sensor_info:
                new_cols[id] = sensor_info[id]['地点名']
            else:
                new_cols[id] = id
        return df.rename(columns=new_cols)

'''
センサごとのアドレス数(population)を取得
'''
def get_population(sday, eday, gr=False,
                   col_by_name=False,
                  tw="10"):
    base_url= 'https://8tops.yamanashi.ac.jp/kofu/bt/'
    if gr:
        server_program="getPopulation_csv2gr.php"
        grStr = "&gr=1"
    else:
        server_program="getPopulation_csv.php"
        grStr = ""
    if tw=="1":
        twStr = "&ts=1"
    else:
        twStr = ""
    
    url2get_population = (base_url + server_program + "?sday=" + sday 
                          + '&eday=' + eday + grStr + twStr)
    res = requests.get(url2get_population).content
    df = pd.read_csv(io.StringIO(res.decode('utf-8')))
    df["date"] = pd.to_datetime(df["Unnamed: 0"])
    df.drop("Unnamed: 0", axis=1, inplace=True)
    df= df.set_index("date")
    # col_by_name=Trueなら列名をセンサ名にする
    if col_by_name:
        df = change_cols_name(df, gr)
    return df

'''
センサペア間の移動アドレス数推移を取得
 (注) root_idはセンサIDで指定（地点名ではなく）
'''
def get_flow_days(sday, eday, gr=0, # gr: for grouped data
                  od="d", # o: root_id is origin. d: destination
                  timeWidth = "60",
                  col_by_name=False,):
    base_url= 'https://8tops.yamanashi.ac.jp/kofu/bt/'
    if gr > 0:
        server_program="getFlowByBT_csv2gr.php"
        grStr = "&gr=" + str(gr)
    else:
        server_program="getFlowByBT_csv.php"
        grStr = ""
        
    url2get_flow = (base_url + server_program + "?sday=" + sday 
                    + '&eday=' + eday
                    + "&od=" + od
                    + "&tw=" + timeWidth
                    + grStr)
    res = requests.get(url2get_flow).content
    df = pd.read_csv(io.StringIO(res.decode('utf-8')))
    # return df
    df["date"] = pd.to_datetime(df["Unnamed: 0"])
    df.drop("Unnamed: 0", axis=1, inplace=True)
    df= df.set_index("date")
    # col_by_name=Trueなら列名をセンサ名にする
    if col_by_name:
        df = change_cols_name(df, gr)
    return df

'''
BTのflow情報をファイルから取る
sday, edayは"yyyy-mm-dd"
'''
def get_flow_days_BT(sday,eday, root_id, od="o",
                     gr=0, timeWidth="60", col_by_name=False):
    src_dir = ble_src_dir + "ble_flow/sum_by_od" + timeWidth
    
    #print(src_dir)
    sdate = dt.strptime(sday, "%Y-%m-%d")
    edate = dt.strptime(eday, "%Y-%m-%d")
    p_date = sdate
    
    df_all = pd.DataFrame()
    while p_date <= edate:
        date_str = p_date.strftime("%Y%m%d")
        if od=="o":
            origin = root_id
            srch_str = (src_dir + "/" 
                        + date_str + "/" + root_id + "*.csv")
        else:
            destination = root_id
            srch_str = (src_dir + "/" 
                        + date_str + "/*_" + root_id + "_*.csv")
        tmp = glob.glob(srch_str)
        for flow_file in tmp: #
            with open(flow_file) as f:
                df = pd.read_csv(f, names=["date", "value"])
                if od == "o":
                    destination = flow_file.split("_")[-2]
                else:
                    origin = flow_file.split("_")[-3]
                    origin = origin.split("/")[-1]
                df['origin'] = origin
                df['destination'] = destination
            df_all = pd.concat([df_all, df], axis=0)
        p_date = p_date + timedelta(days=1)
    #print(len(df_all))
    df_all['date'] = pd.to_datetime(df_all['date'])
    return df_all.sort_values('date')

'''
アドレス数の時間変動の描画
'''

# プロット関数 (for both population and flow)
def plot_bt_data(df, sensors = [], title_str="",
                 date_format='%m-%d %H:%M', figsize=(8,4),
                 xlim="",
                 filename="",
                 legend=""):
    if len(sensors)==0:
        sensors2plot = df.columns.to_list()
    else:
        sensors2plot = sensors
    
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    ax = df.plot(y=sensors2plot, ax=ax, fontsize=12)
    if xlim != "":
        ax.set_xlim(xlim)
    # 凡例は外側に固定
    ax.legend(fontsize=12)
    if(legend == "out"):
        ax.legend(fontsize=12, loc='center left', bbox_to_anchor=(1.0, 0.5))
    ax.set_title(title_str,
                 fontsize=12)
    ax.set_xlabel("date", fontsize=12)
    ax.set_ylabel("アドレス数", fontsize=12)
    
    # ファイル出力 (拡張子はsvgに決め打ち)
    import subprocess
    if filename != "":
        plt.savefig(filename + ".svg", bbox_inches="tight")
        # inkscapeが使える環境なら、次のコマンドでemf形式に変換できる
        subprocess.run("inkscape --file " + filename + ".svg"
                       + " --export-emf " + filename + ".emf", shell=True)
    return (fig,ax)
'''
(plotの応用) センサを個別指定ではなく主要な箇所を選んで描画
'''
def show_major_flows2point(target, from_date, to_date,
                           od="d", tw="60", num=5, gr=1,
                           xlim="", date_format="%m-%d",
                           title_opt="", figsize=(15,4),
                           filename="",
                           legend=""):
    df = get_flow_days(from_date, to_date, target,
                       od=od,
                       gr=gr, timeWidth=tw, col_by_name=True)
    # od
    if od == "o":
        title_tail = "から " + title_opt
    else:
        title_tail = "へ" + title_opt
            
    # sensorごとの総数の算出とソート
    total_nums = df.sum().sort_values(ascending=False)
    # 上位のセンサ名リスト
    sensor2plot = total_nums.index.to_list()
    sensor = getSensorInfo(gr=gr)
    plot_bt_data(df,sensor2plot[:num],
                 title_str=sensor[target]['地点名'] + title_tail,
                date_format=date_format, figsize=figsize,
                 xlim=xlim, filename=filename, legend=legend)

'''
ODを指定して、日々の比較を行うためのデータ取得
'''
def get_flow_od_days(od, sday="", eday="", dayStr="", tw="10", gr=1):
    url= ('https://8tops.yamanashi.ac.jp/kofu/bt/getFlowByBT1link_csv.php?'
          + "o=" + od[0] + "&d=" + od[1] + "&tw=" + tw)
    if len(dayStr)!=0:
        url += "&days=" + dayStr
    else:
        if sday != "":
            url += "&sday=" + sday
        if eday != "":
            url += "&eday=" + eday
    
    if gr > 0:
        url += "&gr=" + str(gr)
    res = requests.get(url).content
    df = pd.read_csv(io.StringIO(res.decode('utf-8')))
    return df

'''
指定されたOD間の１日の流量変化を指定日分重ねて表示
'''
def plot_flow_1link(od, sday="", eday="",days=[], gr=0, figsize=(4,8),
                    title_str="",
                    xlim=[],
                    tw='10',
                    filename="",
                    legend=""):
    
    dayStr = ""
    if len(days) != 0:
        for d in days:
            dayStr += d + ","
        dayStr = dayStr.strip(",")
    df = get_flow_od_days(od, sday=sday, eday=eday, dayStr=dayStr, gr=gr, tw=tw)
    # 時間幅制限
    if len(xlim) == 2:
        df = df[(df['time']>=xlim[0]) & (df['time'] <= xlim[1])]
    
    # 描画
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    df.plot(x="time", ax=ax, fontsize=12)
    # 凡例は外側に固定
    ax.legend(fontsize=12)
    if legend=="out":
        ax.legend(fontsize=12, loc='center left', bbox_to_anchor=(1.0, 0.5))
    ax.set_title(title_str,
                 fontsize=12)
    ax.set_xlabel("date", fontsize=12)
    ax.set_ylabel("アドレス数", fontsize=12)
    
    # ファイル出力 (拡張子はsvgに決め打ち)
    import subprocess
    if filename != "":
        plt.savefig(filename + ".svg", bbox_inches="tight")
        # inkscapeが使える環境なら、次のコマンドでemf形式に変換できる
        subprocess.run("inkscape --file " + filename + ".svg"
                       + " --export-emf " + filename + ".emf", shell=True)
    return (fig,ax) # 呼び出し側で、図に細工できるようにするためaxを返す

# 指定OD、日にち、時間に対して各アドレスの移動時間を返す(サーバ上での実行のみ)
def get_moving_time(date, s_hour, origin, destination, hours=1, gr=2):
    if gr>0:
        src_dir = "/home/raspimngr/csv/ble/kofu/grouped/ble_flow" + str(gr)
    else:
        src_dir = "/home/raspimngr/csv/ble/kofu/ble_flow"
    
    filename = src_dir + "/hop_" + date + ".csv"
    date_hour_s = dt.strptime(date + " " + s_hour, "%Y%m%d %H")
    date_hour_e = date_hour_s + timedelta(hours=hours)
    result = pd.read_csv(filename)
    result['time'] = pd.to_datetime(result['time'], format="%Y-%m-%d %H:%M:%S")
    result = result[(result['travel_time'] < 3600) &
                    (result['time'] >= date_hour_s) & 
                    (result['time'] < date_hour_e) &
                    (result["point"] == origin) & (result["fwd"] == destination)]
    
    return result

def plot_histogram_moving_time(date, s_hour, origin, destination,
                               hours=1,
                               bins=60, # 刻み幅
                               gr=2,
                               figsize=(8,6),
                               max_time=0, # x軸の上限 (秒)
                               out_filename=""):
    # センサ名称
    sensor = getSensorInfo(gr)
    # データ取得
    df = get_moving_time(date, s_hour, origin, destination, hours, gr)
    # 描画
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    if max_time == 0:
        df["travel_time"].hist(bins=bins, ax=ax)
    else:
        df["travel_time"].hist(bins=bins, range=[0,max_time], ax=ax)
    ax.set_title(sensor[origin]['地点名'] + "から" + sensor[destination]['地点名']
                 + "の移動時間分布 (" + date + " "
                 + str(s_hour) + "時から" + str(hours) + "時間分" + ")")
    print(len(df))
    ax.text(ax.get_xlim()[1]*0.8, ax.get_ylim()[1]*0.9, "全数: " + str(len(df)),
            fontsize=12)
    ax.set_xlabel("移動時間(秒)")
    ax.set_ylabel("検出アドレス数")
    
    # ファイル出力 (拡張子はsvgに決め打ち)
    import subprocess
    if out_filename != "":
        plt.savefig(out_filename + ".svg", bbox_inches="tight")
        # inkscapeが使える環境なら、次のコマンドでemf形式に変換できる
        subprocess.run("inkscape --file " + out_filename + ".svg"
                       + " --export-emf " + out_filename + ".emf", shell=True)
    return (fig,ax) # 呼び出し側で、図に細工できるようにするためaxを返す
        
    

'''
Wi-FiのflowデータをMySQLから取得
Return: DataFrame
'''
def get_flow_days_WiFi(sdate,edate, root_id, od="o"): # date format: yyyy-mm-dd
    import mysql.connector as mysql
    # DB関係基本設定
    conn = mysql.connect(
        host="bdpserv.yamanashi.ac.jp",
        user="develuser",
        passwd="uy&&nii",
        database="wifi_kofu")
    
    cur = conn.cursor()
    
    # query
    table_name = "flow_all_trunc10"
    if od == "o":
        od_cond = " and origin=" + root_id.replace("kofu","")
    else:
        od_cond = " and destination=" + root_id.replace("kofu","")
        
    # destination = "9"
    # stime = '8'
    #etime = '9'
    sql_str = ('select yearday, hour, origin, destination, number as num from '
               + " flow_all_trunc10 "
               + ' where yearday >= "' + sdate + '" and yearday <= "' + edate + '"'
               + od_cond + " and glbit=0")
    cur.execute(sql_str)
    data = []
    for d in cur:
        data.append([d[0], d[1], 'kofu' + str(d[2]), 'kofu'+ str(d[3]), d[4]])

    df = pd.DataFrame(data,
                      columns=['date', 'hour', 'origin', 'destination', 'value'])
    df['date'] = pd.to_datetime(df['date'])
    df['date_str'] = df['date'].dt.strftime("%Y-%m-%d")
    df['date1'] = df['date_str'] + " " + df['hour'].str.zfill(2) + ":00:00"
    df['date'] = pd.to_datetime(df['date1'])
    df = df.sort_values('date')
    return df[['date','origin', 'destination', 'value', 'hour']]

'''
指定した期間の、root_id <> targets(複数) の流動の時間変動をプロット
'''
def plotFlowByBLE(sday, eday, root_id, od, targets,
                  title_str="" , out_dir=""):
    flow_BLE = get_flow_days_BT(sday, eday, root_id, od=od)
    rename_list = {}
    contains_str = ""
    for id in targets:
        contains_str = contains_str + id + "|"
    contains_str = contains_str.rstrip("|")
    if od == "o":
        flow_BLE = flow_BLE[flow_BLE.destination.str.contains(contains_str)]
    else:
        flow_BLE = flow_BLE[flow_BLE.origin.str.contains(contains_str)]
    #print(sensorNameDictById(targets))
    flow_BLE = flow_BLE.replace(sensorNameDictById(targets))
    plt.rcParams["font.size"] = 14
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(12,6))
    hue_str = "destination"
    if od == "d":
        hue_str = "origin"
    sns.lineplot(data=flow_BLE, x='date', y='value', hue=hue_str, ax = ax)
    if title_str == "":
        if od == "o":
            title_str = sensorNameById(root_id) + "からの流動数（BLE計測）"
        else:
            title_str = sensorNameById(root_id) + "への流動数（BLE計測）"
    ax.set_title(title_str)
    if out_dir != "":
        out_filename = (out_dir + "/" + root_id
                        + "_" + sday + "_" + eday + "_" + od)
        plt.savefig(out_filename + ".svg")
        subprocess.run("inkscape --file " + out_filename + ".svg"
                       + " --export-emf " + out_filename + ".emf", shell=True)

def plotTransition4hourBLE(sday, eday, points, hour4plot="08:00", width="1H",
                          title_str="",
                          figsize=(10,5),
                          population_url=population_url): # ex. hour4plot = "08:00" width="1H"
    width_in_title = {"1H": "１時間", "10T": "10分間", "30T": "30分間"}
    # 指定した時間(hour4plot)のpopulationの推移を描画
    url = population_url + "?sday=" + sday + "&eday=" + eday
    res = requests.get(url).content
    csv_str = io.StringIO(res.decode('utf-8'))
    df = pd.read_csv(csv_str)
    df['date'] = pd.to_datetime(df["Unnamed: 0"])
    #
    # df.plot(x = "date", y = points)
    # dateをhourでまとめ、平均をとる
    df["date_h"]= df["date"].dt.floor("1H") # 四捨五入はround
    df_h = df.groupby("date_h").mean()
    df_h = df_h.reset_index("date_h")
    df_h = df_h.set_index("date_h")
    df_h = df_h.at_time("08:00")
    df_h = df_h.reset_index()
    # 描画 
    df4plot = change_cols_name(df_h, gr=0)

    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=figsize)
    df4plot.plot(x= "date_h", y=sensorNamesByIds(points), ax=ax)
    ax.set_title(title_str +"の滞留人口 ("+ hour4plot + "から10分ごとに計測した値の" + width_in_title[width] + "の平均)")
    ax.set_xlabel("年月日")
    ax.set_ylabel("BLEアドレス数")
    return fig, df4plot.copy()

def getPopulationData(sday, eday):
    url = population_url + "?sday=" + sday + "&eday=" + eday
    res = requests.get(url).content
    csv_str = io.StringIO(res.decode('utf-8'))
    df = pd.read_csv(csv_str)
    df['date'] = pd.to_datetime(df["Unnamed: 0"])
    df = df.set_index('date')
    return df.drop("Unnamed: 0", axis=1).copy()

def getPoints():
    res = requests.get(kofu_base_url + "sensor_points.php").content
    df = pd.read_json(io.StringIO(res.decode('utf-8')))
    df = df.T
    df['id'] = df.index
    ret_list = []
    tmp_dict = df.to_dict(orient='list')
    for i, id in enumerate(tmp_dict['id']):
        ret_list.append({'id': id, 'name': tmp_dict['name'][i],
                          'lat': tmp_dict['lat'][i], 'lon': tmp_dict['lon'][i]})
    return ret_list
    
    
    
