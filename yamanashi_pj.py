# -*- coding: utf-8 -*-

import streamlit as st
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from datetime import datetime as dt, timedelta

# sys.path.append("./")
from functions4kofu import *
from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Hiragino Maru Gothic Pro', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
kitaguchi = ["kofu27", "kofu40", "kofu41"]
minamiguchi = ["kofu25", "kofu42", "kofu28"]
marunouchi = ["kofu9", "kofu22", "kofu23"]
chuo = ["kofu17", "kofu3", "kofu13", "kofu24"]
sday = "20220101"
eday = "20220121"


def main():
    # タイトル
    st.sidebar.title('山梨県内の群流計測')

    # 関数定義
    def showPopulationData():
        for k in st.session_state.points.keys():
            if ("pop_" + k in st.session_state and
             st.session_state["pop_" +k]):
                st.write(k)
        if "population_df" in st.session_state:
            st.dataframe(st.session_state.population_df)
    
    def plotPopulationData():
        #show_line_chart_btn = st.button("streamlitのline_chart表示")
        #if show_line_chart_btn:
        st.line_chart(st.session_state.population_df)
        # showPopulationData()
    
    st.sidebar.markdown('## 1. BLEによる人口動態データ')
    # マークダウンテキスト
    st.sidebar.markdown('各センサのデータを10分ごとに集計した時系列表示')
    #st.sidebar.button

    population_url = "https://8tops.yamanashi.ac.jp/kofu/bt/getPopulation_csv.php"
    
    # st.write("表示期間を指定してください。")
    sdate = st.sidebar.date_input("開始日", dt(2021,12,26))
    # st.text("〜")
    edate = st.sidebar.date_input("終端日", dt.now())
    use_btn = st.sidebar.button("データ更新")
    if use_btn:
        if not "population_df" in st.session_state:
            st.session_state.population_df = getPopulationData(
                sdate.strftime("%Y%m%d"),
                edate.strftime("%Y%m%d"))
    st.sidebar.button("データ表示", key="sw4population",
                    on_click=showPopulationData)
    points = {}
    check_box4points = []
    for p in getPoints():
        #st.write(p['name'])
        points[p['id']] = p['name']
        if "pop_" + p['id'] in st.session_state:
            flg = True
        else:
            flg = False
        st.sidebar.checkbox(p['name'], flg, key = "pop_" + p['id'])
            
    st.session_state.points = points
    
    # st.text(sdate.strftime("%Y-%m-%d") + "〜" + edate.strftime("%Y-%m-%d"))
    # if show_btn:
    #     # show_points = []
    #     # for p in check_box_point:
    #     #     show_points.append(p['id'])
    #     # st.write(show_points)
    #     fig,df = plotTransition4hourBLE(sdate.strftime("%Y%m%d"),
    #                                     edate.strftime("%Y%m%d"),
    #                                     kitaguchi, "07:00", "1H",
    #                                     title_str = "甲府駅北口 ",
    #                                     population_url=population_url)
    #     st.pyplot(fig)
    #     df = df.set_index('date_h')
    #     show_df_btn = st.button("テーブル表示")
    #     if show_df_btn:
    #         st.dataframe(df)
    #     show_line_chart_btn = st.button("streamlitのline_chart表示")
    #     if show_line_chart_btn:
    #         st.line_chart(df)

    
    st.sidebar.markdown("## 2. 二地点間流動")

    # 群流



if __name__ == '__main__':
    main()
    
