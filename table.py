import pandas as pd
from openpyxl import Workbook

# 读取原始数据
df = pd.read_csv("answers.csv")

# 计算百分比统计
percentage_stats = (
    df.groupby("question_id")["answer"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
    .rename("percentage")
    .reset_index()
)

# 创建一个新的 Excel 工作簿
wb = Workbook()
wb.remove(wb.active)  # 删除默认的空 sheet

# 按问题拆分并保存到不同的 sheet
for question, group in percentage_stats.groupby("question_id"):
    ws = wb.create_sheet(title=str(question)[:30])  # Excel sheet 名不能超过 31 个字符
    ws.append(["answer", "percentage"])  # 表头
    for _, row in group.iterrows():
        ws.append([row["answer"], row["percentage"]])

# 保存文件
wb.save("answers_percentage_stats.xlsx")