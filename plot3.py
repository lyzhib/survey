import pandas as pd
import plotly.express as px
import os
import re

file_path = "survey results.csv"
df = pd.read_csv(file_path)

output_dir = "pie_charts_html"
os.makedirs(output_dir, exist_ok=True)

def safe_filename(name):
    """
    将列名转换为 Windows 安全的文件名
    """
    name = re.sub(r'[\\/:*?"<>|]', '', name)  # 移除非法字符
    name = name.strip()
    return name

for column in df.columns:
    value_counts = (
        df[column]
        .value_counts(dropna=False)
        .reset_index()
    )
    value_counts.columns = ["Answer", "Count"]

    fig = px.pie(
        value_counts,
        names="Answer",
        values="Count",
        title=f"Вопрос：{column}",
        hole=0
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig.update_layout(
        title_x=0.5,
        legend_title_text="Варианты ответов"
    )

    safe_name = safe_filename(column)
    output_path = os.path.join(output_dir, f"{safe_name}.html")

    fig.write_html(output_path)

print("✅ Все круговые диаграммы успешно сохранены в формате HTML")