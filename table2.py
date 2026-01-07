import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import plotly.express as px

# 读取 CSV
csv_path = "survey results.csv"  # 请替换为你的实际路径
df = pd.read_csv(csv_path, low_memory=False)

# 目标列
col = "Что, на ваш взгляд, следует улучшить в организации проектного обучения в вашем вузе?"

# 提取非空回答
texts = df[col].dropna().astype(str).map(lambda s: re.sub(r"[^а-яА-Я\s]", " ", s.lower()))

# 自定义俄语停用词（你可以根据需要扩充）
russian_stopwords = [
    "и", "в", "во", "не", "что", "на", "с", "как", "а", "то", "все", "для",
    "это", "по", "при", "быть", "который", "своей", "более", "менее", "уже",
    "или", "если", "но", "их", "его", "ее", "чтобы", "также", "вот"
]

# 关键词频率分析
vectorizer = CountVectorizer(stop_words=russian_stopwords, max_features=40)
X = vectorizer.fit_transform(texts)
word_counts = np.asarray(X.sum(axis=0)).ravel()
words = vectorizer.get_feature_names_out()

freq_df = pd.DataFrame({"Слово": words, "Частота": word_counts})
freq_df = freq_df.sort_values(by="Частота", ascending=False)

# ------------------------------
# 📌 关键词频率图：从左到右递减（纵向）
# ------------------------------
fig1 = px.bar(
    freq_df,
    x="Слово",                   # 横轴为词语
    y="Частота",                 # 纵轴为频率
    color="Частота",
    color_continuous_scale="Viridis",
    text="Частота",
    title="Часто упоминаемые слова: что улучшить в проектном обучении"
)

fig1.update_traces(texttemplate="%{text}", textposition="outside")

fig1.update_layout(
    xaxis_title="Слово",
    yaxis_title="Частота",
    plot_bgcolor="white",
    xaxis_tickangle=-45,
    xaxis={
        "categoryorder": "array",
        "categoryarray": freq_df["Слово"].tolist()  # 从左到右按频率递减
    }
)

# ------------------------------
# 主题建模 (LDA)
# ------------------------------
n_topics = 4
lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, max_iter=20)
lda.fit(X)

feature_names = vectorizer.get_feature_names_out()
topics = []
for idx, comp in enumerate(lda.components_):
    top_idx = comp.argsort()[::-1][:8]
    top_words = [feature_names[i] for i in top_idx]
    topics.append(top_words)

doc_topic = lda.transform(X)
topic_assign = doc_topic.argmax(axis=1)
counts = np.bincount(topic_assign, minlength=n_topics)
topic_pct = counts / counts.sum() * 100

topic_labels = [f"T{t}: {', '.join(topics[t])}" for t in range(n_topics)]

dist_df = pd.DataFrame({"Тема": topic_labels, "Число ответов": counts, "Процент": topic_pct})
dist_df = dist_df.sort_values(by="Число ответов", ascending=False)

# ------------------------------
# 📌 主题分布图：从左到右递减（纵向）
# ------------------------------
fig2 = px.bar(
    dist_df,
    x="Тема",
    y="Число ответов",
    color="Процент",
    color_continuous_scale="Blues",
    text="Процент",
    title="Распределение тем: предложения по улучшению проектного обучения"
)

fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

fig2.update_layout(
    xaxis_tickangle=30,
    plot_bgcolor="white",
    xaxis={
        "categoryorder": "array",
        "categoryarray": dist_df["Тема"].tolist()  # 从左到右按数量递减
    }
)

# 显示图表
fig1.show(renderer="browser")
fig2.show(renderer="browser")

# 输出主题词
print("Темы и ключевые слова:")
for t, words in enumerate(topics):
    print(f"Тема {t}: {', '.join(words)}")

print("\nРаспределение тем (%):")
for t, pct in enumerate(topic_pct):
    print(f"T{t}: {pct:.1f}%")
