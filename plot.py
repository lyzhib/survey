import pandas as pd
import plotly.express as px

# 读取 CSV 文件
file_path = "answers.csv"   # 确保和脚本在同一目录
df = pd.read_csv(file_path)

# 按问题和答案统计次数
counts = df.groupby(["question_id", "answer"]).size().reset_index(name="count")

# 转换为百分比（使用 transform 保持索引）
counts["percent"] = counts.groupby("question_id")["count"].transform(lambda x: x / x.sum() * 100)

# 输出 HTML 文件
html_output = "answers_charts.html"
with open(html_output, "w", encoding="utf-8") as f:
    for question, group in counts.groupby("question_id"):
        # 按百分比排序，从高到低
        group_sorted = group.sort_values("percent", ascending=False)

        fig = px.bar(
            group_sorted,
            x="answer",
            y="percent",
            text=group_sorted["percent"].round(1).astype(str) + "%",
            title=f"Распределение ответов: {question}",
            labels={"answer": "Ответ", "percent": "Процент (%)"},
            color="percent",  # 根据百分比上色
            color_continuous_scale="Blues",  # 渐变色
        )

        fig.update_traces(textposition="outside")

        # x 轴按百分比从高到低排序
        fig.update_layout(
            xaxis={'categoryorder':'array', 'categoryarray': group_sorted['answer']},
            margin=dict(l=50, r=20, t=50, b=100),
            coloraxis_colorbar=dict(title="Процент (%)")
        )

        f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))

print(f"✅ 交互式图表已导出: {html_output}")