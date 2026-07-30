# Analisis Research Canvas

## Artikel

**Smart Healthcare AI for ICD-10 Code Prediction from Unstructured Clinical Texts: A Comparative Study of Four Machine Learning Models**

Artikel ini membahas prediksi kode ICD-10 dari teks klinis tidak terstruktur menggunakan empat model machine learning klasik: Naive Bayes, Random Forest, Support Vector Machine (SVM), dan XGBoost. Fokus utama penelitian adalah menemukan model yang tidak hanya akurat, tetapi juga efisien untuk diterapkan pada lingkungan rumah sakit dengan keterbatasan infrastruktur komputasi.

## Research Canvas

| Elemen | Analisis |
|---|---|
| Judul / Fokus Riset | Prediksi kode ICD-10 dari teks klinis tidak terstruktur menggunakan empat model machine learning klasik: Naive Bayes, Random Forest, SVM, dan XGBoost. |
| Latar Belakang | Banyak rumah sakit masih melakukan pengkodean ICD-10 secara manual. Proses ini lambat, rawan kesalahan, dan membebani coder medis. Tantangan semakin besar karena catatan klinis sering berbentuk teks bebas, singkatan, bahasa campuran, dan tidak standar. |
| Masalah Riset | Bagaimana membangun model prediksi ICD-10 yang akurat, cepat, hemat memori, dan cocok diterapkan di rumah sakit dengan keterbatasan infrastruktur, khususnya dalam konteks data klinis Bahasa Indonesia. |
| Research Gap | Sebagian besar studi sebelumnya memakai data berbahasa Inggris, data EHR yang lebih terstruktur, atau model deep learning yang mahal secara komputasi. Masih sedikit studi yang membandingkan model ringan pada teks diagnosis Bahasa Indonesia serta menguji aspek deployment seperti latency, throughput, dan penggunaan memori. |
| Tujuan Penelitian | Mengevaluasi dan membandingkan performa empat model machine learning klasik untuk klasifikasi ICD-10 dari catatan klinis tidak terstruktur, baik dari sisi akurasi klasifikasi maupun efisiensi sistem. |
| Dataset | 92.000 rekam diagnosis tidak terstruktur dari empat rumah sakit swasta di Indonesia. Data berasal dari 12 kode ICD-10 paling sering pada tiap rumah sakit. Label ICD-10 diberikan secara manual oleh coder medis tersertifikasi. |
| Metode Preprocessing | Normalisasi teks, lowercasing, penghapusan tanda baca, angka, stopword umum, dan stopword medis seperti "mg" atau "patient". |
| Feature Extraction | Menggunakan TF-IDF untuk mengubah teks diagnosis menjadi representasi numerik. Pilihan ini sesuai dengan target riset karena TF-IDF ringan, mudah diterapkan, dan kompatibel dengan model klasik. |
| Model yang Dibandingkan | Naive Bayes, SVM linear, Random Forest, dan XGBoost. |
| Metrik Evaluasi | Dua kelompok metrik digunakan: metrik klasifikasi, yaitu accuracy, precision, recall, F1-score; dan metrik sistem, yaitu latency, throughput, serta peak memory usage. |
| Lingkungan Eksperimen | PythonAnywhere free tier dengan 1 shared CPU core dan 512 MB RAM. Ini sengaja dipilih untuk mensimulasikan keterbatasan sumber daya komputasi rumah sakit. |
| Hasil Utama | XGBoost menjadi model terbaik secara keseluruhan, baik dari sisi performa klasifikasi maupun efisiensi sistem. Naive Bayes unggul untuk throughput dan cocok untuk pemrosesan cepat. SVM memberi keseimbangan antara akurasi dan latency. Random Forest cukup baik secara klasifikasi, tetapi kurang ideal untuk sistem real-time karena latency tinggi dan throughput rendah. |
| Kontribusi Penelitian | Artikel ini berkontribusi pada penerapan AI kesehatan di konteks Indonesia, terutama untuk otomasi ICD-10 berbasis teks klinis Bahasa Indonesia dengan pendekatan model ringan yang realistis untuk rumah sakit berinfrastruktur terbatas. |
| Keterbatasan | Artikel belum banyak menjelaskan distribusi detail tiap kelas ICD-10, strategi menangani imbalance, validasi lintas rumah sakit, interpretabilitas prediksi, serta perbandingan dengan model NLP modern seperti IndoBERT atau model transformer medis. |
| Peluang Riset Lanjutan | Penelitian berikutnya dapat menguji model berbasis transformer Bahasa Indonesia, pendekatan hybrid TF-IDF dan embedding, explainable AI untuk membantu coder medis, validasi eksternal antar rumah sakit, serta deployment dalam sistem rekam medis elektronik nyata. |

## Analisis Naratif

Artikel ini menempatkan masalah pengkodean ICD-10 sebagai persoalan penting dalam sistem kesehatan. ICD-10 tidak hanya dipakai untuk dokumentasi diagnosis, tetapi juga untuk klaim pembiayaan, pelaporan kesehatan publik, pemantauan penyakit, dan analitik rumah sakit. Karena itu, kesalahan atau keterlambatan dalam pengkodean dapat berdampak langsung pada operasional rumah sakit.

Konteks Indonesia menjadi nilai penting dalam penelitian ini. Banyak riset otomatisasi ICD-10 sebelumnya berfokus pada dataset berbahasa Inggris dan lingkungan EHR yang lebih matang. Artikel ini mencoba mengisi celah tersebut dengan memakai data diagnosis berbahasa Indonesia dari empat rumah sakit. Data semacam ini cenderung lebih bervariasi karena mengandung singkatan, istilah medis, bentuk penulisan tidak baku, dan kemungkinan campuran bahasa.

Pilihan menggunakan TF-IDF dan model machine learning klasik cukup masuk akal untuk tujuan penelitian. Model seperti Naive Bayes, SVM, Random Forest, dan XGBoost relatif lebih ringan dibandingkan deep learning atau large language model. Dalam konteks rumah sakit dengan infrastruktur terbatas, efisiensi ini penting karena model harus bisa berjalan cepat, hemat memori, dan mudah diintegrasikan ke sistem operasional.

Dari sisi hasil, XGBoost menjadi model paling unggul secara umum. Model ini mampu menangkap hubungan fitur yang lebih kompleks dibandingkan Naive Bayes atau SVM sederhana, sekaligus tetap efisien. Naive Bayes tetap memiliki posisi penting karena sangat cepat dan cocok untuk skenario throughput tinggi. SVM berada di tengah sebagai model yang seimbang, sedangkan Random Forest memiliki performa klasifikasi yang baik tetapi kurang ideal untuk sistem real-time karena latency dan penggunaan sumber dayanya lebih besar.

Kekuatan utama artikel ini adalah evaluasinya tidak berhenti pada akurasi. Penulis juga menilai latency, throughput, dan penggunaan memori. Ini membuat penelitian lebih dekat dengan kebutuhan deployment nyata, bukan hanya eksperimen laboratorium. Pendekatan ini relevan untuk smart healthcare karena sistem AI kesehatan harus dapat digunakan dalam alur kerja klinis yang cepat dan terbatas secara sumber daya.

Namun, artikel masih memiliki beberapa keterbatasan. Penjelasan tentang distribusi kelas ICD-10 belum cukup rinci, padahal data medis biasanya tidak seimbang. Artikel juga belum banyak membahas analisis kesalahan, misalnya kode mana yang paling sering tertukar dan apakah kesalahan tersebut berdampak klinis serius. Selain itu, interpretabilitas model belum dieksplorasi secara mendalam, padahal dalam konteks medis, coder dan tenaga kesehatan perlu memahami alasan di balik rekomendasi kode.

## Kesimpulan

Secara keseluruhan, artikel ini menunjukkan bahwa model machine learning klasik masih relevan untuk otomasi prediksi ICD-10, terutama di lingkungan rumah sakit dengan keterbatasan sumber daya. XGBoost menjadi kandidat paling kuat karena memberikan kombinasi performa klasifikasi dan efisiensi sistem yang baik. Meski demikian, penelitian lanjutan masih diperlukan untuk menguji generalisasi model, meningkatkan interpretabilitas, menangani imbalance data, dan membandingkan pendekatan klasik dengan model NLP modern berbasis Bahasa Indonesia.
