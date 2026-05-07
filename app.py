import streamlit as st
import pandas as pd
import time
import requests
import json
from datetime import datetime

# ================= 核心配置区 =================
APP_ID = "460c98cb78358245d9784a840af5ae58"
API_KEY = "b95b4de3639c785f747c03db5c536341"
BMOB_URL = "https://api.bmobcloud.com/1/classes/EloRecord"

HEADERS = {
    "X-Bmob-Application-Id": APP_ID,
    "X-Bmob-REST-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 🎯 极致减负：每位受试者随机抽做的题量
MAX_TASKS = 40 

st.set_page_config(page_title="景象偏好盲测", page_icon="👀", layout="centered")

# ================= 📱 手机端防折叠 CSS 魔法 =================
st.markdown("""
<style>
    /* 强制所有列在手机端保持并排，绝不折叠换行 */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    /* 调整图片圆角和紧凑度 */
    .stImage > img {
        border-radius: 6px;
    }
    div[data-testid="column"] {
        padding: 0 4px !important; 
    }
    /* 去除顶部多余留白 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    /* 让按钮文字小一点，适应手机屏幕 */
    .stButton > button {
        font-size: 14px !important;
        padding: 0.25rem 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 核心数据驱动 =================
@st.cache_data
def load_data():
    return pd.read_csv("ELO_Matchups.csv")

def save_to_bmob(expert_id, img_a, img_b, winner, response_time, match_idx):
    data = {
        "expert_id": expert_id,
        "image_a": img_a,
        "image_b": img_b,
        "winner": winner,
        "response_time_sec": response_time,
        "match_index": int(match_idx),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.post(BMOB_URL, headers=HEADERS, data=json.dumps(data), timeout=3)
    except:
        pass 

# 🎭 模糊化标题：防止受试者过度思考
st.markdown("<h2 style='text-align: center;'>👀 场景视觉偏好快速测试</h2>", unsafe_allow_html=True)

# 初始化受试者状态
if 'expert_id' not in st.session_state:
    st.session_state.expert_id = None
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'user_matches' not in st.session_state:
    st.session_state.user_matches = pd.DataFrame()
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# ================= 1. 登录页 (文案已极致优化) =================
if not st.session_state.expert_id:
    st.info(f"💡 **测试说明**：\n\n欢迎参与本次【视觉偏好匿名盲测】！\n\n本测试旨在收集大众对不同场景的直觉偏好。请不要刻意分析图片细节，完全依靠您的**第一直觉**，选出您觉得【更舒适、更好看】的那一张。\n\n本组测试共 **{MAX_TASKS} 题**，全程仅需约 1 分钟，感谢您的支持！")
    
    # 隐私安抚文案
    expert_id_input = st.text_input("请输入您的代号或昵称 (仅用于后台区分数据，严格保密，请放心填写)：", max_chars=15)
    
    if st.button("🚀 我已了解，开始测试", type="primary", use_container_width=True):
        if expert_id_input:
            st.session_state.expert_id = expert_id_input
            # 🎲 为该用户随机抽出 40 题
            all_matches = load_data()
            st.session_state.user_matches = all_matches.sample(n=MAX_TASKS).reset_index()
            st.session_state.start_time = time.time()
            st.rerun()
        else:
            st.error("请输入一个代号以便进入测试哦！")

# ================= 2. 核心打分框架 =================
else:
    if st.session_state.current_q >= MAX_TASKS:
        st.success(f"🎉 恭喜 **{st.session_state.expert_id}**！您已完成全部 {MAX_TASKS} 题！数据已安全传至后台。")
        st.balloons()
        st.write("您可以直接退出网页或关闭微信窗口，感谢您对科研的巨大贡献！")
    else:
        current_match = st.session_state.user_matches.iloc[st.session_state.current_q]
        img_a_name = current_match['Image_A']
        img_b_name = current_match['Image_B']
        original_idx = current_match['index'] 

        # 进度条
        progress = st.session_state.current_q / MAX_TASKS
        st.progress(progress)
        st.caption(f"受试者: **{st.session_state.expert_id}** | 当前进度: **{st.session_state.current_q + 1} / {MAX_TASKS}**")

        # 📱 完美适配手机的并排图片区
        col1, col2 = st.columns(2)
        with col1:
            st.image(f"images/{img_a_name}", caption="👈 场景 A")
        with col2:
            st.image(f"images/{img_b_name}", caption="场景 B 👉")

        st.markdown("<h4 style='text-align: center; margin-top: 0; margin-bottom: 15px;'>哪边的场景感觉更舒适？</h4>", unsafe_allow_html=True)
        
        # 打分逻辑
        def record_vote(winner):
            resp_time = round(time.time() - st.session_state.start_time, 3)
            save_to_bmob(st.session_state.expert_id, img_a_name, img_b_name, winner, resp_time, original_idx)
            st.session_state.current_q += 1
            st.session_state.start_time = time.time()
            st.rerun()

        # 📱 完美适配手机的并排按钮区 (权重比例调整为更易点击)
        b_col1, b_col2, b_col3 = st.columns([4, 3, 4])
        with b_col1:
            if st.button("选 A 👈", type="primary", use_container_width=True): record_vote("A")
        with b_col2:
            if st.button("平局", use_container_width=True): record_vote("Tie")
        with b_col3:
            if st.button("选 B 👉", type="primary", use_container_width=True): record_vote("B")
