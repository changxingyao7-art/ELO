import streamlit as st
import pandas as pd
import time
import requests
import json
from datetime import datetime

# ================= 核心配置区 =================
# 你的 Bmob 云端账本钥匙
APP_ID = "460c98cb78358245d9784a840af5ae58"
API_KEY = "b95b4de3639c785f747c03db5c536341"
BMOB_URL = "https://api.bmobcloud.com/1/classes/EloRecord"

HEADERS = {
    "X-Bmob-Application-Id": APP_ID,
    "X-Bmob-REST-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 网页全局设置 (适配手机端)
st.set_page_config(page_title="城市街道视觉质量感知评估", page_icon="🏙️", layout="centered")

# ================= 核心函数区 =================
@st.cache_data
def load_data():
    # 载入对阵表
    return pd.read_csv("ELO_Matchups.csv")

def save_to_bmob(expert_id, img_a, img_b, winner, response_time, match_idx):
    # 整理数据并暗中打上时间戳，发往 Bmob 云端
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
        requests.post(BMOB_URL, headers=HEADERS, data=json.dumps(data))
    except Exception as e:
        pass # 防止个别网络波动卡死界面

# ================= UI 界面与交互 =================
st.title("🏙️ 城市街道视觉环境感知评估")

# 1. 状态初始化与断点记忆
if 'expert_id' not in st.session_state:
    st.session_state.expert_id = None
if 'match_idx' not in st.session_state:
    st.session_state.match_idx = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# 2. 身份验证页
if not st.session_state.expert_id:
    st.info("欢迎参与华中三大城市街道感知联合评估！该系统已嵌入时间戳探针，请根据第一直觉真实作答。")
    expert_id_input = st.text_input("请输入您的专家编号/姓名缩写 (如: Expert_01):")
    if st.button("开始评估 🚀", use_container_width=True):
        if expert_id_input:
            st.session_state.expert_id = expert_id_input
            st.session_state.start_time = time.time()
            st.rerun()
        else:
            st.error("专家编号不能为空！")

# 3. 核心打分框架
else:
    df_matches = load_data()
    total_matches = len(df_matches)

    if st.session_state.match_idx >= total_matches:
        st.success(f"🎉 恭喜 {st.session_state.expert_id}，您已完成所有打分任务！数据已安全归档，感谢您的学术贡献！")
    else:
        current_match = df_matches.iloc[st.session_state.match_idx]
        img_a_name = current_match['Image_A']
        img_b_name = current_match['Image_B']

        # 进度条显示
        progress = (st.session_state.match_idx) / total_matches
        st.progress(progress)
        st.caption(f"专家: **{st.session_state.expert_id}** | 进度: **{st.session_state.match_idx + 1} / {total_matches}**")

        # 图片并排显示
        col1, col2 = st.columns(2)
        with col1:
            st.image(f"images/{img_a_name}", caption="👈 图片 A", use_column_width=True)
        with col2:
            st.image(f"images/{img_b_name}", caption="👉 图片 B", use_column_width=True)

        st.markdown("### 👁️ 哪条街道的**视觉质量/宜居度**更好？")
        
        # 记录打分逻辑
        def record_vote(winner):
            # 精准计算毫秒级反应时间
            resp_time = round(time.time() - st.session_state.start_time, 3)
            # 云端落盘
            save_to_bmob(st.session_state.expert_id, img_a_name, img_b_name, winner, resp_time, st.session_state.match_idx)
            # 进入下一题
            st.session_state.match_idx += 1
            st.session_state.start_time = time.time()
            st.rerun()

        # 三大投票按钮
        b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
        with b_col1:
            if st.button("👈 图片 A 更好", type="primary", use_container_width=True): record_vote("A")
        with b_col2:
            if st.button("平局 / 难分伯仲", use_container_width=True): record_vote("Tie")
        with b_col3:
            if st.button("图片 B 更好 👉", type="primary", use_container_width=True): record_vote("B")
