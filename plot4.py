import pandas as pd
import plotly.express as px
import os
import re

# ===== 读取数据 =====
file_path = "survey results.csv"
df = pd.read_csv(file_path)

# ===== 输出目录 =====
html_dir = "bar_percent_html"
png_dir  = "bar_percent_png"
os.makedirs(html_dir, exist_ok=True)
os.makedirs(png_dir, exist_ok=True)

# ===== 安全文件名（Windows 兼容）=====
def safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()

# ===== 逐列绘图 =====
for col in df.columns:

    # 统计数量
    counts = df[col].value_counts(dropna=False).reset_index()
    counts.columns = ["Answer", "Count"]

    # 计算百分比
    total = counts["Count"].sum()
    counts["Percent"] = counts["Count"] / total * 100

    # 按百分比从高到低排序
    counts = counts.sort_values("Percent", ascending=False)

    # ===== 竖向百分比条形图 =====
    fig = px.bar(
        counts,
        x="Answer",
        y="Percent",
        color="Answer",                 # 每个选项不同颜色
        text=counts["Percent"].map(lambda x: f"{x:.1f}%"),
        title=f"Вопрос：{col}",
    )

    fig.update_layout(
        template="simple_white",
        title_x=0.5,
        xaxis_title="Варианты ответов",
        yaxis_title="Проценты (%)",
        yaxis_range=[0, 100],
        showlegend=False                # 颜色已由 x 轴说明
    )

    fig.update_traces(
        textposition="outside"
    )

    # ===== 保存 =====
    safe = safe_filename(col)
    fig.write_html(os.path.join(html_dir, f"{safe}.html"))
    fig.write_image(os.path.join(png_dir, f"{safe}.png"),
                    width=900, height=600)

print("✅ Все вертикальные процентные шкалы сгенерированы (HTML + PNG)")