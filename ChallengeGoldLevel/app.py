import os
import pandas as pd
import re
import sqlite3
from flask import Flask, request, jsonify
from flasgger import Swagger
import yaml

# Fungsi untuk memuat file dan membersihkan data dari file CSV mentah
def load_and_clean_data():
    # Dapatkan path absolut
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, 'data/dataset.csv')
    abusive_path = os.path.join(current_dir, './data/abusive.csv')
    kamusalay_path = os.path.join(current_dir, './data/new_kamusalay.csv')

    # Membaca file CSV
    try:
        # Membaca file CSV dalam mode byte
        with open(dataset_path, 'rb') as f:
            raw_data = f.read()
        with open(abusive_path, 'rb') as f:
            raw_abusive = f.read()
        with open(kamusalay_path, 'rb') as f:
            raw_kamusalay = f.read()

        # Decode byte data dengan errors='replace' untuk karakter yang tidak bisa di-decode
        decoded_data = raw_data.decode('utf-8', errors='replace')
        decoded_abusive = raw_abusive.decode('utf-8', errors='replace')
        decoded_kamusalay = raw_kamusalay.decode('utf-8', errors='replace')

        # Simpan data yang sudah didecode ke dalam CSV sementara (sebagai string)
        with open('data/decoded_dataset.csv', 'w', encoding='utf-8') as f:
            f.write(decoded_data)
        with open('data/decoded_abusive.csv', 'w', encoding='utf-8') as f:
            f.write(decoded_abusive)
        with open('data/decoded_kamusalay.csv', 'w', encoding='utf-8') as f:
            f.write(decoded_kamusalay)

        # Membaca kembali file CSV yang sudah dibersihkan ke dalam pandas
        dataset = pd.read_csv('data/decoded_dataset.csv')
        abusive_words = pd.read_csv('data/decoded_abusive.csv')
        kamusalay = pd.read_csv('data/decoded_kamusalay.csv', header=None, names=['alay_word', 'normal_word'])
        
        print("Files loaded and cleaned successfully")
        return dataset, abusive_words, kamusalay
    except Exception as e:
        print(f"Error loading or decoding files: {e}")
        return None, None, None

# Fungsi pembersihan teks
def cleansing_text(text, kamusalay, abusive_words):
    text = text.lower()
    text = re.sub(r'\\x[\da-fA-F]{2}|\\n|\\t|[\t]', ' ', text)  # Hapus escape chars
    text = re.sub(r'(\d\s*)+', ' ', text)  # Hapus urutan angka yang tidak relevan
    
    for _, row in kamusalay.iterrows():
        text = re.sub(r'\b{}\b'.format(re.escape(row['alay_word'])), row['normal_word'], text, flags=re.IGNORECASE)
    for word in abusive_words['ABUSIVE']:
        text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text, flags=re.IGNORECASE)

    text = re.sub(r'(\b\w+)(\d+)', lambda x: f"{x.group(1)}-{x.group(1)}", text)  # Tangani pengulangan
    text = re.sub(r'[^a-zA-Z\s]', '', text).strip()  # Hapus karakter non-alfabet
    return text

# Fungsi untuk menyimpan data ke dalam SQLite
def save_to_sqlite(dataset):
    try:
        conn = sqlite3.connect('tweets.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cleaned_tweets (
                id INTEGER PRIMARY KEY,
                original_tweet TEXT,
                cleaned_tweet TEXT
            )
        ''')

        for _, row in dataset.iterrows():
            cursor.execute('INSERT INTO cleaned_tweets (original_tweet, cleaned_tweet) VALUES (?, ?)',
                           (row['Tweet'], row['cleaned_tweet']))
        
        conn.commit()
        print("Data saved to SQLite successfully")
    except Exception as e:
        print(f"Error during SQLite operations: {e}")
    finally:
        conn.close()

# Fungsi untuk menjalankan Flask API
def start_flask_app(kamusalay, abusive_words):
    app = Flask(__name__)

    with open('./docs/swagger.yml', 'r') as file:
        swagger_template = yaml.safe_load(file)
    swagger = Swagger(app, template=swagger_template)

    @app.route('/clean_text', methods=['POST'])
    def clean_text():
        try:
            text = request.form.get('text', '')
            cleaned_text = cleansing_text(text, kamusalay, abusive_words)
            return jsonify({"cleaned_text": cleaned_text}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/upload_csv', methods=['POST'])
    def upload_csv():
        try:
            file = request.files['file']
            df = pd.read_csv(file)
            if 'Tweet' not in df.columns:
                return jsonify({"error": "No 'tweet' column found in the file"}), 400

            df['cleaned_tweet'] = df['Tweet'].apply(lambda x: cleansing_text(x, kamusalay, abusive_words))
            return jsonify(df[['Tweet', 'cleaned_tweet']].to_dict(orient="records")), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/test', methods=['GET'])
    def test_route():
        return "Server is running!"

    app.run(debug=True)

# Fungsi utama untuk mengatur alur kerja aplikasi
def main():
    dataset, abusive_words, kamusalay = load_and_clean_data()
    if dataset is None:
        print("Failed to load the data.")
        return

    # Cleansing data
    dataset['cleaned_tweet'] = dataset['Tweet'].apply(lambda x: cleansing_text(x, kamusalay, abusive_words))
    dataset.to_csv('data/cleaned_dataset_final.csv', index=False)
    print("Cleaned dataset saved successfully")

    # Save to SQLite
    save_to_sqlite(dataset)

    # Start Flask app
    start_flask_app(kamusalay, abusive_words)

if __name__ == '__main__':
    main()