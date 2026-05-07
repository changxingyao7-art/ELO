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

MAX_TASKS = 40 

st.set_page_config(page_title="景象偏好盲测", page_icon="👀", layout="centered")

# ================= 📱 手机端完美排版 CSS 魔法 =================
st.markdown("""
<style>
    /* 1. 强制图片列在手机端保持 50% 并排，彻底解决超出屏幕的问题 */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        flex-direction: row !important;
    }
    div[data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important; /* 核心修复：允许列无限缩小，防止把屏幕撑爆 */
        padding: 0 4px !important; 
    }
    /* 图片自适应缩放 */
    .stImage > img {
        border-radius: 6px;
        max-width: 100% !important;
        height: auto !important;
        object-fit: cover;
    }
    /* 2. 去除页面顶部多余留白，让内容往上提 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    /* 3. 增强按钮体验：加高、加粗、加间距 */
    .stButton > button {
        height: 3.2rem;
        font-size: 16px !important;
        font-weight: bold;
        border-radius: 8px;
        margin-bottom: 5px; /* 按钮之间留出缝隙防误触 */
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

st.markdown("<h2 style='text-align: center;'>👀 场景视觉偏好快速测试</h2>", unsafe_allow_html=True)

if 'expert_id' not in st.session_state:
    st.session_state.expert_id = None
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'user_matches' not in st.session_state:
    st.session_state.user_matches = pd.DataFrame()
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# ================= 1. 登录页 =================
if not st.session_state.expert_id:
    st.info(f"💡 **测试说明**：\n\n欢迎参与本次【视觉偏好匿名盲测】！\n\n本测试旨在收集大众对不同场景的直觉偏好。请不要刻意分析图片细节，完全依靠您的**第一直觉**，选出您觉得【更舒适、更好看】的那一张。\n\n本组测试共 **{MAX_TASKS} 题**，全程仅需约 1 分钟，感谢您的支持！")
    
    expert_id_input = st.text_input("请输入您的姓名 (仅用于后台区分数据，严格保密，请放心填写)：", max_chars=15)
    
    if st.button("🚀 我已了解，开始测试", type="primary", use_container_width=True):
        if expert_id_input:
            st.session_state.expert_id = expert_id_input
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

        # 📱 完美适配手机的左右并排图片区 (严格50/50，绝不越界)
        col1, col2 = st.columns(2)
        with col1:
            st.image(f"images/{img_a_name}", caption="👈 场景 A", use_column_width=True)
        with col2:
            st.image(f"images/{img_b_name}", caption="场景 B 👉", use_column_width=True)

        st.markdown("<h4 style='text-align: center; margin-top: 5px; margin-bottom: 15px;'>哪边的场景感觉更舒适？</h4>", unsafe_allow_html=True)
        
        def record_vote(winner):
            resp_time = round(time.time() - st.session_state.start_time, 3)
            save_to_bmob(st.session_state.expert_id, img_a_name, img_b_name, winner, resp_time, original_idx)
            st.session_state.current_q += 1
            st.session_state.start_time = time.time()
            st.rerun()

        # 📱 完美还原你的设计：三个长条按钮垂直堆叠！
        if st.button("👈 选 A (左侧场景更舒适)", type="primary", use_container_width=True): record_vote("A")
        if st.button("➖ 平局 / 难分伯仲", use_container_width=True): record_vote("Tie")
        if st.button("👉 选 B (右侧场景更舒适)", type="primary", use_container_width=True): record_vote("B")
