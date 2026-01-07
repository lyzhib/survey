import pandas as pd
import plotly.express as px
import os
import re

# 读取数据
df = pd.read_csv("answers.csv")

# 创建保存 HTML 的文件夹
output_dir = "charts_html"
os.makedirs(output_dir, exist_ok=True)

# 清理文件名函数
def clean_filename(s):
    return re.sub(r'[<>:"/\\|?*]', '_', s)

# 为每个问题生成单独 HTML
for question, group in df.groupby("question_id"):
    counts = group["answer"].value_counts().reset_index()
    counts.columns = ["answer", "count"]

    fig = px.pie(
        counts,
        names="answer",
        values="count",
        title=f"Вопрос: {question}",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")

    # 保存为 HTML 文件，清理文件名
    filename = f"{output_dir}/question_{clean_filename(str(question))}.html"
    fig.write_html(filename, include_plotlyjs='cdn', full_html=True)

    print(f"Сгенерировать файл: {filename}")