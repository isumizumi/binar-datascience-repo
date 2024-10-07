import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud

# Memuat data yang sudah dibersihkan
df = pd.read_csv('data/cleaned_dataset_final.csv')

# Menampilkan nama kolom dalam DataFrame
print("Kolom yang ada di DataFrame:", df.columns)

# Menampilkan 5 baris pertama untuk pengecekan
print(df.head())

# Plot distribusi hate speech
plt.figure(figsize=(8, 6))

# Menggunakan nama kolom yang benar dari hasil print
sns.countplot(x='hs', data=df)

plt.title("Distribusi Hate Speech di Tweet")
plt.xlabel("Hate Speech (1 = Ada, 0 = Tidak Ada)")
plt.ylabel("Jumlah Tweet")
plt.show()

# Plot distribusi abusive speech
plt.figure(figsize=(8, 6))
sns.countplot(x='abusive', data=df)
plt.title("Distribusi Abusive Speech di Tweet")
plt.xlabel("Abusive Speech (1 = Ada, 0 = Tidak Ada)")
plt.ylabel("Jumlah Tweet")
plt.show()

# Menggabungkan semua tweet menjadi satu teks
all_tweets = " ".join(df['cleaned_tweet'])

# Membagi teks menjadi kata-kata
words = all_tweets.split()

# Menghitung frekuensi kata
word_counts = Counter(words)

# Memuat kata-kata abusive dari file abusive.csv
abusive_words = pd.read_csv('data/cleaned_abusive.csv')['ABUSIVE'].tolist()

# Filter kata-kata abusive dari word_counts
abusive_word_counts = {word: count for word, count in word_counts.items() if word in abusive_words}

# Buat DataFrame dari kata-kata abusive
abusive_df = pd.DataFrame(list(abusive_word_counts.items()), columns=['word', 'count']).sort_values(by='count', ascending=False)

# Visualisasi 10 kata abusive paling umum
plt.figure(figsize=(10, 6))
sns.barplot(x='count', y='word', data=abusive_df.head(10))
plt.title("10 Kata Abusive Paling Umum di Tweet")
plt.xlabel("Jumlah Kemunculan")
plt.ylabel("Kata Abusive")
plt.show()

# Buat wordcloud dari kata-kata abusive
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(abusive_word_counts)

# Tampilkan wordcloud
plt.figure(figsize=(10, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title("Wordcloud dari Kata Abusive di Tweet")
plt.show()