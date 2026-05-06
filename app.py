import pandas as pd
import numpy as np
import os
import shutil
import random
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ================= 配置区 =================
# 你存放 5000 张原始图片的文件夹路径
ORIGINAL_IMG_DIR = r"C:\Users\86188\Desktop\shai xuan ELO"
# 你的 6 大指标 CSV 路径
CSV_PATH = r"C:\Users\86188\Desktop\Visual_Metrics_Final_4.csv"

# 即将生成的供网页版使用的文件夹和文件
OUTPUT_IMG_DIR = r"C:\Users\86188\Desktop\ELO_Web\images"
OUTPUT_MATCHUPS = r"C:\Users\86188\Desktop\ELO_Web\ELO_Matchups.csv"

# 抽样目标
TOTAL_SAMPLES = 1000
CLUSTERS = 50  # 聚成50类
SAMPLES_PER_CLUSTER = TOTAL_SAMPLES // CLUSTERS
MATCHES_PER_IMAGE = 6 # 每张图参与对决的次数 (总对决数大约 3000 场)
# ==========================================

def scientific_sampling():
    print("🚀 正在读取 5000 张街景物理指标...")
    df = pd.read_csv(CSV_PATH)
    
    # 1. 提取 6 大指标进行标准化
    features = ['GVI', 'UCL', 'BVI', 'PVI', 'VVI', 'DI']
    X = df[features].values
    X_scaled = StandardScaler().fit_transform(X)
    
    # 2. K-Means 聚类 (分层)
    print(f"🧠 正在执行 K-Means 聚类，将街道分为 {CLUSTERS} 种典型风貌...")
    kmeans = KMeans(n_clusters=CLUSTERS, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(X_scaled)
    
    # 3. 均匀抽样
    print(f"🎯 正在从每个风貌类中抽取 {SAMPLES_PER_CLUSTER} 张代表性图像...")
    sampled_df = df.groupby('Cluster').apply(lambda x: x.sample(n=min(len(x), SAMPLES_PER_CLUSTER), random_state=42)).reset_index(drop=True)
    
    selected_images = sampled_df['Image_Name'].tolist()
    print(f"✅ 成功精选出 {len(selected_images)} 张高代表性图像！")
    
    # 4. 物理复制文件到网页专用文件夹
    print(f"📁 正在将精选图像复制到网页库: {OUTPUT_IMG_DIR}")
    if not os.path.exists(OUTPUT_IMG_DIR):
        os.makedirs(OUTPUT_IMG_DIR)
        
    copied_count = 0
    for img_name in selected_images:
        src = os.path.join(ORIGINAL_IMG_DIR, img_name)
        dst = os.path.join(OUTPUT_IMG_DIR, img_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_count += 1
    print(f"✅ 成功复制 {copied_count} 张图像！")
    
    # 5. 生成对阵表
    print(f"⚔️ 正在为精选图像安排对阵表...")
    all_matches = set()
    for img in selected_images:
        opponents = random.sample([x for x in selected_images if x != img], MATCHES_PER_IMAGE)
        for opp in opponents:
            match = tuple(sorted([img, opp]))
            all_matches.add(match)
            
    match_df = pd.DataFrame(list(all_matches), columns=['Image_A', 'Image_B'])
    
    # 打乱对战顺序
    match_df = match_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    os.makedirs(os.path.dirname(OUTPUT_MATCHUPS), exist_ok=True)
    match_df.to_csv(OUTPUT_MATCHUPS, index=False, encoding='utf-8-sig')
    
    print(f"🎉 大功告成！共生成 {len(match_df)} 场巅峰对决，对阵表已保存至: {OUTPUT_MATCHUPS}")
    print("👉 接下来，你只需要把生成的 ELO_Web 文件夹里的代码传到 GitHub 即可！")

if __name__ == "__main__":
    scientific_sampling()