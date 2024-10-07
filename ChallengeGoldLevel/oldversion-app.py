import os
import pandas as pd
import re

import sqlite3

from flask import Flask, request, jsonify
from flasgger import Swagger

import yaml


##STEP 0. Memastikan data ada di path yang sesuai
print("Starting the script...")

# Dapatkan path absolut
current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(current_dir, 'data/dataset.csv')
abusive_path = os.path.join(current_dir, './data/abusive.csv')
kamusalay_path = os.path.join(current_dir, './data/new_kamusalay.csv')
print("Paths set correctly")

# Baca file dalam mode byte
try:
    with open(dataset_path, 'rb') as file:
        raw_dataset = file.read()
    print("Dataset file read successfully")
    
    with open(abusive_path, 'rb') as file:
        raw_abusive = file.read()
    print("Abusive file read successfully")
    
    with open(kamusalay_path, 'rb') as file:
        raw_kamusalay = file.read()
    print("Kamusalay file read successfully")
except Exception as e:
    print(f"Error reading files: {e}")

# Decode byte data ke UTF-8, abaikan karakter yang tidak valid
try:
    cleaned_dataset = raw_dataset.decode('utf-8', errors='ignore')
    cleaned_abusive = raw_abusive.decode('utf-8', errors='ignore')
    cleaned_kamusalay = raw_kamusalay.decode('utf-8', errors='ignore')
    print("Decoding of files successful")
except Exception as e:
    print(f"Error decoding files: {e}")

# Simpan kembali ke file CSV yang baru
try:
    cleaned_dataset_path = os.path.join(current_dir, 'data/cleaned_dataset.csv')
    with open(cleaned_dataset_path, 'w', encoding='utf-8') as new_file:
        new_file.write(cleaned_dataset)
    print(f"Cleaned dataset saved to {cleaned_dataset_path}")

    cleaned_abusive_path = os.path.join(current_dir, 'data/cleaned_abusive.csv')
    with open(cleaned_abusive_path, 'w', encoding='utf-8') as new_file:
        new_file.write(cleaned_abusive)
    print(f"Cleaned abusive file saved to {cleaned_abusive_path}")

    cleaned_kamusalay_path = os.path.join(current_dir, 'data/cleaned_kamusalay.csv')
    with open(cleaned_kamusalay_path, 'w', encoding='utf-8') as new_file:
        new_file.write(cleaned_kamusalay)
    print(f"Cleaned kamusalay file saved to {cleaned_kamusalay_path}")
except Exception as e:
    print(f"Error saving cleaned files: {e}")


##STEP 1. Membaca dataset & Cleansing Text

try:
    # Membaca file CSV
    dataset = pd.read_csv(cleaned_dataset_path)
    abusive_words = pd.read_csv(cleaned_abusive_path)
    kamusalay = pd.read_csv(cleaned_kamusalay_path, header=None, names=['alay_word', 'normal_word'])
    
    print("Dataset, abusive words, and kamusalay loaded successfully")
except Exception as e:
    print(f"Error loading CSV files: {e}")

# print(dataset.head())
# print(abusive_words.head())
# print(kamusalay.head())

# Ubah semua nama kolom menjadi huruf kecil
dataset.columns = dataset.columns.str.lower()
print("Column names converted to lowercase")

# Fungsi untuk membersihkan text dari kata alay dan abusive
def cleansing_text(text):
    print(f"Original text: {text}")
    
    # Step 1: Ubah semua teks menjadi huruf kecil
    text = text.lower()

    # Step 2: Bersihkan karakter escape seperti \n, \t, \xf0\x9f\x98\x84, dll.
    text = re.sub(r'\\x[\da-fA-F]{2}', '', text)  # Hilangkan \xf0\x9f dll.
    text = re.sub(r'\\n', ' ', text)  # Hilangkan \n
    text = re.sub(r'\\t', ' ', text)  # Hilangkan \t
    text = re.sub(r'[\t]', ' ', text)  # Hilangkan tab

    # Step 3: Hapus urutan angka dan karakter yang tidak relevan seperti \t1\t0\t...
    text = re.sub(r'(\d\s*)+', ' ', text)  # Menghapus angka berurutan atau angka terpisah dengan spasi/tab
    
    # Step 4: Ganti kata alay dengan kata normal berdasarkan kamus alay (contoh fiktif)
    for i, row in kamusalay.iterrows():
        text = re.sub(r'\b{}\b'.format(re.escape(row['alay_word'])), row['normal_word'], text, flags=re.IGNORECASE)
    
    # Step 5: Hapus kata-kata abusive
    for word in abusive_words['ABUSIVE']:
        text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text, flags=re.IGNORECASE)
    
    # Step 6: Tangani kata dengan angka yang menunjukkan pengulangan (contoh: "cantik2" menjadi "cantik-cantik")
    text = re.sub(r'(\b\w+)(\d+)', lambda x: f"{x.group(1)}-{x.group(1)}", text)

    # Step 7: Hilangkan karakter non-alfabet yang tersisa
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Menghapus karakter non-alfabet
    
    # Step 8: Hilangkan spasi berlebih yang mungkin muncul setelah pembersihan
    text = re.sub(r'\s+', ' ', text).strip()

    print(f"Cleaned text: {text}")
    return text

# Terapkan cleansing pada seluruh dataset
try:
    dataset['cleaned_tweet'] = dataset['tweet'].apply(cleansing_text)
    print("Cleansing of tweets successful")
except Exception as e:
    print(f"Error during cleansing tweets: {e}")

# Tampilkan hasil cleansing
try:
    print(dataset[['tweet', 'cleaned_tweet']].head())
except Exception as e:
    print(f"Error displaying cleaned dataset: {e}")

# Simpan Dataset yang sudah dibersihkan
try:
    dataset.to_csv('data/cleaned_dataset_final.csv', index=False)
    print("Cleaned dataset saved successfully to 'data/cleaned_dataset_final.csv'")
except Exception as e:
    print(f"Error saving cleaned dataset: {e}")


## STEP 2. Menyimpan Data ke SQLite
try:
    # Membuat koneksi ke SQLite
    conn = sqlite3.connect('tweets.db')
    cursor = conn.cursor()
    print("Connected to SQLite")

    # Membuat tabel jika belum ada
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cleaned_tweets (
        id INTEGER PRIMARY KEY,
        original_tweet TEXT,
        cleaned_tweet TEXT
    )
    ''')
    print("Table created/verified")

    # Menyimpan data ke tabel
    for i, row in dataset.iterrows():
        cursor.execute('''
        INSERT INTO cleaned_tweets (original_tweet, cleaned_tweet)
        VALUES (?, ?)
        ''', (row['tweet'], row['cleaned_tweet']))
    
    conn.commit()
    print("Data committed to SQLite")
except Exception as e:
    print(f"Error during SQLite operations: {e}")
finally:
    conn.close()
    print("Connection to SQLite closed")


## STEP 3. Membuat API dengan Flask
app = Flask(__name__)

# Konfigurasi Swagger untuk menggunakan file YAML
with open('./docs/swagger.yml', 'r') as file:
    swagger_template = yaml.safe_load(file)

swagger = Swagger(app, template=swagger_template)

# Route untuk membersihkan teks langsung melalui POST request
@app.route('/clean_text', methods=['POST'])
def clean_text():
    """
    Endpoint untuk membersihkan teks dari kata abusive dan alay
    ---
    parameters:
      - name: text
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Teks setelah dibersihkan
    """
    try:
        if 'text' not in request.form:
            return jsonify({"error": "No text provided"}), 400
        
        text = request.form['text']
        cleaned_text = cleansing_text(text)
        return jsonify({"cleaned_text": cleaned_text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route untuk menerima file CSV dan membersihkan tweet di dalamnya
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """
    Endpoint untuk upload file CSV berisi tweet dan membersihkan isinya
    ---
    parameters:
      - name: file
        in: formData
        type: file
        required: true
    responses:
      200:
        description: File CSV setelah di-cleansing
    """
    try:
        # Periksa apakah file dikirimkan dengan request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")

        # Membaca file CSV
        df = pd.read_csv(file)
        print(f"CSV Loaded. Columns: {df.columns}")

        # Periksa apakah kolom tweet ada
        if 'Tweet' not in df.columns:
            return jsonify({"error": "No 'tweet' column found in the file"}), 400
        
        # Terapkan fungsi cleansing_text ke kolom tweet
        df['cleaned_tweet'] = df['Tweet'].apply(cleansing_text)
        print("Tweets cleaned")

        # Kembalikan hasil pembersihan sebagai JSON
        return jsonify(df[['Tweet', 'cleaned_tweet']].to_dict(orient="records")), 200
    except Exception as e:
        print(f"Error in upload_csv endpoint: {e}")
        return jsonify({"error": str(e)}), 500


# Route sederhana untuk pengujian server
@app.route('/test', methods=['GET'])
def test_route():
    return "Server is running!"

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)