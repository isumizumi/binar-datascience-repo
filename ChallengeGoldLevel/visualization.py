import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Fungsi untuk memuat dan membersihkan data
def load_and_clean_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, 'data/dataset.csv')
    abusive_path = os.path.join(current_dir, './data/abusive.csv')
    kamusalay_path = os.path.join(current_dir, './data/new_kamusalay.csv')

    # Baca file CSV dalam mode byte
    with open(dataset_path, 'rb') as f:
        raw_data = f.read()
    with open(abusive_path, 'rb') as f:
        raw_abusive = f.read()
    with open(kamusalay_path, 'rb') as f:
        raw_kamusalay = f.read()

    # Decode byte data dengan errors='replace'
    decoded_data = raw_data.decode('utf-8', errors='replace')
    decoded_abusive = raw_abusive.decode('utf-8', errors='replace')
    decoded_kamusalay = raw_kamusalay.decode('utf-8', errors='replace')

    # Simpan data yang sudah didecode ke CSV sementara
    with open('cleaned_dataset.csv', 'w', encoding='utf-8') as f:
        f.write(decoded_data)
    with open('cleaned_abusive.csv', 'w', encoding='utf-8') as f:
        f.write(decoded_abusive)
    with open('cleaned_kamusalay.csv', 'w', encoding='utf-8') as f:
        f.write(decoded_kamusalay)

    # Membaca kembali file CSV yang sudah dibersihkan
    dataset = pd.read_csv('cleaned_dataset.csv')
    abusive_words = pd.read_csv('cleaned_abusive.csv')
    kamusalay = pd.read_csv('cleaned_kamusalay.csv', header=None, names=['alay_word', 'normal_word'])

    # Lihat struktur data
    print("Struktur Dataset:")
    print(dataset.info())
    
    print("\nStruktur Abusive Words:")
    print(abusive_words.info())
    
    print("\nStruktur Kamusalay:")
    print(kamusalay.info())

    # Lihat statistik deskriptif
    print("\nStatistik Dataset:")
    print(dataset.describe())

    return dataset, abusive_words, kamusalay

# Fungsi untuk membersihkan teks dari kata alay dan abusive
def cleansing_text(text, kamusalay, abusive_words):
    text = text.lower()
    text = re.sub(r'\\x[\da-fA-F]{2}', '', text)  # Hapus escape chars
    text = re.sub(r'\\n|\\t', ' ', text)  # Hapus \n, \t
    text = re.sub(r'(\d\s*)+', ' ', text)  # Hapus urutan angka yang tidak relevan
    
    # Ganti kata alay dengan kata normal
    for _, row in kamusalay.iterrows():
        text = re.sub(r'\b{}\b'.format(re.escape(row['alay_word'])), row['normal_word'], text, flags=re.IGNORECASE)
    
    # Hapus kata abusive
    for word in abusive_words['ABUSIVE']:
        text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text, flags=re.IGNORECASE)
    
    # Hilangkan karakter non-alfabet yang tersisa
    text = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    
    return text

# Fungsi utama untuk melakukan eksplorasi data dan visualisasi
def main():
    # Muat dan bersihkan data
    dataset, abusive_words, kamusalay = load_and_clean_data()

    # Terapkan pembersihan pada kolom tweet
    dataset['cleaned_tweet'] = dataset['Tweet'].apply(lambda x: cleansing_text(x, kamusalay, abusive_words))

    # Simpan dataset yang sudah dibersihkan
    dataset.to_csv('cleaned_dataset_final.csv', index=False)
    print("Dataset sudah dibersihkan dan disimpan ke 'cleaned_dataset_final.csv'")

    # 1. Visualisasi Distribusi Hate Speech
    plt.figure(figsize=(10, 5))
    ax = sns.countplot(x='HS', data=dataset)
    plt.title('Distribusi Hate Speech di Tweet')
    plt.xlabel('Hate Speech (1 = Ada, 0 = Tidak Ada)')
    plt.ylabel('Jumlah Tweet')

    # Tambahkan nilai di atas bar
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='baseline', fontsize=12, color='black', xytext=(0, 5),
                    textcoords='offset points')
    plt.show()

    # 2. Visualisasi Distribusi Abusive Speech
    plt.figure(figsize=(10, 5))
    ax = sns.countplot(x='Abusive', data=dataset)
    plt.title('Distribusi Abusive Speech di Tweet')
    plt.xlabel('Abusive Speech (1 = Ada, 0 = Tidak Ada)')
    plt.ylabel('Jumlah Tweet')

    # Tambahkan nilai di atas bar
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='baseline', fontsize=12, color='black', xytext=(0, 5),
                    textcoords='offset points')
    plt.show()

    # 3. Visualisasi Korelasi Antar Variabel Hate Speech (Heatmap)
    hs_columns = ['HS', 'HS_Individual', 'HS_Group', 'HS_Religion', 'HS_Race', 'HS_Physical',
                  'HS_Gender', 'HS_Other', 'HS_Weak', 'HS_Moderate', 'HS_Strong']
    correlation_matrix = dataset[hs_columns].corr()

    plt.figure(figsize=(12, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Korelasi Antar Variabel Hate Speech')
    plt.show()

    # 4. Visualisasi Perbandingan Hate Speech dan Abusive Speech
    dataset['HS_Abusive'] = dataset.apply(lambda row: 'HS & Abusive' if row['HS'] == 1 and row['Abusive'] == 1
                                          else 'HS Only' if row['HS'] == 1
                                          else 'Abusive Only' if row['Abusive'] == 1
                                          else 'Neither', axis=1)

    plt.figure(figsize=(10, 5))
    ax = sns.countplot(x='HS_Abusive', data=dataset)
    plt.title('Perbandingan Hate Speech dan Abusive Speech')
    plt.xlabel('Kategori')
    plt.ylabel('Jumlah Tweet')

    # Tambahkan nilai di atas bar
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='baseline', fontsize=12, color='black', xytext=(0, 5),
                    textcoords='offset points')
    plt.show()

if __name__ == '__main__':
    main()
