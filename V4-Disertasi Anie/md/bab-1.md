# PENDAHULUAN

## Latar Belakang

Interoperabilitas sistem informasi kesehatan merupakan kebutuhan kritis dalam ekosistem kesehatan modern, di mana data medis harus dapat dipertukarkan dan diintegrasikan antar berbagai sistem dan institusi (Ayuningtyas et al., 2025). Tanpa interoperabilitas, data medis akan terisolasi dalam silo-silo sistem yang menghambat integrasi dan pemanfaatan data secara holistik untuk kepentingan klinis maupun penelitian (Rinaldi et al., 2023). Dalam konteks tersebut, pertukaran data saja belum cukup. Interoperabilitas baru bernilai apabila data yang dipertukarkan dipahami dengan makna yang sama oleh sistem yang berbeda.

Makna yang sama tersebut berkaitan langsung dengan konsistensi semantik, yaitu kemampuan sistem kesehatan yang berbeda untuk tidak hanya bertukar data secara struktural, tetapi juga memahami arti data tersebut secara konsisten. Tanpa konsistensi semantik, informasi klinis yang secara kasat mata tampak serupa dapat ditafsirkan secara berbeda oleh sistem yang berbeda, sehingga menurunkan kualitas integrasi data, analisis, dan pengambilan keputusan klinis. Karena itu, konsistensi semantik merupakan prasyarat utama bagi interoperabilitas yang benar-benar dapat digunakan.

Fast Healthcare Interoperability Resource (FHIR), yang dikembangkan Health Level Seven (HL7), merupakan salah satu standar interoperabilitas untuk mendukung pertukaran data kesehatan dalam format digital secara syntactic dan semantic dan digunakan secara luas. Berdasarkan laporan dari HL7 International & Firely pada bulan Mei 2025, paling tidak ada 52 negara yang dilaporkan menggunakan FHIR secara aktif, termasuk Indonesia ([https://hl7chile.cl/wp-content/uploads/2025/06/2025-State-of-FHIR-Survey-Report.pdf](https://hl7chile.cl/wp-content/uploads/2025/06/2025-State-of-FHIR-Survey-Report.pdf)). Apabila FHIR dapat dianggap sebagai framework pertukaran data, maka SNOMED CT (Systematized Nomenclature of Medicine-Clinical Terms), LOINC (Logical Observation Identifiers Names and Codes), ICD (International Statistical Classification of Diseases) adalah standar terminologi dan klasifikasi klinis/ data yang mengisi FHIR.

Penggunaan standar terminologi klinis yang diakui secara internasional tersebut memastikan bahwa konsep klinis direpresentasikan secara seragam, menghilangkan ambiguitas dan memungkinkan pertukaran data yang akurat lintas platform (Bidgood, 1998). Dengan kata lain, interoperabilitas teknis tanpa standardisasi terminologi tetap akan menyisakan persoalan pada level makna klinis.

SNOMED CT adalah terminologi klinis paling komprehensif dan multibahasa di dunia yang dikelola oleh SNOMED International, dirancang untuk merepresentasikan konsep klinis secara detail, mulai dari gejala, diagnosis, prosedur, temuan, hingga obat-obatan, dengan hierarki dan relasi semantik yang kaya ([https://www.snomed.org/](https://www.snomed.org/)). Setiap konsep dalam SNOMED CT memiliki pengidentifikasi permanen yang secara unik merepresentasikan makna klinis tertentu. Di sisi lain, LOINC adalah standar yang dikembangkan oleh Regenstrief Institute untuk mengidentifikasi hasil observasi laboratorium dan klinis secara universal, seperti tes darah, urinalisis, tanda vital, dan parameter fisiologis ([https://loinc.org/](https://loinc.org/)). LOINC menyediakan kode universal untuk setiap jenis pengukuran atau observasi, sehingga memfasilitasi pertukaran dan penggabungan hasil klinis untuk perawatan, manajemen outcomes, dan penelitian (Ayuningtyas et al., 2025). Sementara itu, ICD adalah sistem klasifikasi penyakit yang dikelola oleh Organisasi Kesehatan Dunia (WHO), digunakan terutama untuk koding diagnosis dan prosedur kesehatan dengan tujuan statistik, manajemen kesehatan, dan pembiayaan. Perbedaan peran SNOMED CT, LOINC, dan ICD menunjukkan bahwa kebutuhan standarisasi data klinis tidak dapat dipenuhi oleh satu sistem terminologi saja: SNOMED CT unggul dalam kedalaman klinis, LOINC dalam identifikasi observasi, dan ICD dalam klasifikasi administratif dan epidemiologis. Bahkan secara resmi dinyatakan bahwa dengan kelengkapan terminologinya, SNOMED-CT dapat dipetakan ke standar internasional lain seperti ICD-10 dan ICD-9 CM. Tabel 1.1 menggambarkan perbedaan representasi kode untuk Diabetes Melitus Tipe 2 di ketiga standar tersebut, yang secara visual mempertegas bahwa masing-masing terminologi memiliki fungsi yang spesifik dan saling melengkapi, bukan menggantikan. 

**Tabel 1.1. Perbedaan Representasi Kode Diabetes Melitus Tipe 2 di SNOMED CT, LOINC, dan ICD-10**

| Aspek Informasi Pasien | SNOMED CT | LOINC | ICD-10 |
| :---- | :---- | :---- | :---- |
| **Apa yang dikodekan?** | Konsep klinis (diagnosis, gejala, temuan, prosedur) | Pertanyaan observasi (tes, pengukuran, dokumen) | Diagnosis (penyakit, cedera, penyebab kematian) |
| **Kode & Nama** | 44054006—Type 2 diabetes mellitus | 14771-9—Glucose \[Mass/volume\] in Capillary blood by Glucometer—fasting | E11.9—Type 2 diabetes mellitus without complications |
| **Informasi tambahan yang bisa ditangkap** | Lokasi anatomi (pankreas) | Nilai hasil tes (numerik: 126 mg/dL) | Komplikasi spesifik (E11.2 dengan komplikasi ginjal) |
|  | Severitas (misal: terkontrol/tidak) | Waktu pengambilan sampel (puasa, 2 jam *post prandial*) | Ketoasidosis (E11.1) |
|  | Etiologi (misal: karena obesitas) | Metode pengukuran (glukometer, serum) | Koma diabetik (E11.0) |
|  | Komplikasi (nefropati, retinopati) | Satuan (mg/dL, mmol/L) | Tidak dapat menangkap detail anatomi atau etiologi secara rinci |
|  | Riwayat pengobatan | — | — |

Dalam konteks interoperabilitas kesehatan nasional, sebagaimana diimplementasikan melalui platform SATUSEHAT, ketiganya digunakan secara simultan, dimana data diagnosis wajib merujuk pada ICD-10, data observasi/laboratorium menggunakan LOINC, dan terminologi klinis rinci menggunakan SNOMED CT. Meskipun demikian, **SATUSEHAT belum menyediakan fitur pemetaan otomatis yang dapat mengonversi secara langsung antar terminologi. Tetapi** infrastruktur pendukung pemetaan telah dipersiapkan dalam bentuk panduan dan dokumentasi, di antaranya: (1) panduan penggunaan SNOMED-CT *terminology browser* untuk melakukan pemetaan antara kode lokal dengan SNOMED-CT *concept* yang sepadan; (2) buku panduan penggunaan terminologi LOINC yang memuat langkah-langkah pemetaan LOINC; (3) video tutorial pembelajaran mandiri untuk LOINC dan panduan mendaftar lisensi afiliasi SNOMED CT; serta (4) dokumentasi SNOMED-CT yang menjelaskan bahwa terminologi ini dapat dipetakan ke standar internasional lain seperti ICD-10, ICD-9 CM, dan LOINC. P**latform menyediakan "peta jalan" dan alat bantu, namun proses pemetaan dari data lokal ke terminologi standar tetap menjadi tanggung jawab pengembang/vendor EMR untuk dilakukan secara manual atau melalui sistem yang mereka bangun sendiri.**

Kesenjangan ini memaksa pengembang untuk melakukan proses pemetaan secara manual, yang menjadi salah satu *pain points* utama sebagaimana diidentifikasi dalam penelitian Heryawan dkk. (2025). Urgensi otomasi pemetaan antar terminologi klinis semakin mendesak. Tanpa pemetaan terstruktur, data lintas fasilitas tidak dapat diolah secara bermakna, menghambat interoperabilitas sebagai fondasi sistem kesehatan digital nasional. 

Hal yang harus dipertimbangkan adalah bahwa pemetaan terminologi klinis menuntut kemampuan khusus, berbeda dengan pemetaan di bidang lain (misalnya e-commerce, perpustakaan, atau pendidikan), karena hal-hal berikut.  

1. Perlunya pemahaman struktur ontologi yang dalam (relasi, atribut, post-coordination) (Kate, 2020; Park et al., 2026).  
2. Kemampuan menangani istilah komposit melalui dekomposisi dan penalaran (Gilani et al., 2025).  
3. Perlunya ekstraksi entitas dari teks naratif panjang sebelum pemetaan (Eslami et al., 2026; Peterson & Liu, 2020).  
4. Memiliki toleransi terhadap variasi bahasa ekstrem (teks panjang, singkatan, typo, istilah lokal, multilingual) (Chen et al., 2022).  
5. Akurasi sangat tinggi karena berdampak langsung pada keselamatan pasien (Yu et al., 2026).  
6. Kepatuhan terhadap standar dan regulasi (misalnya FHIR). Pertukaran data kesehatan wajib mengikuti standar interoperabilitas tertentu. Di Indonesia, SATUSEHAT mewajibkan penggunaan format FHIR dan terminologi SNOMED CT, LOINC, ICD-10.  
7. Evaluasi oleh ahli klinis karena tidak ada gold standard otomatis (Chen et al., 2022; Eslami et al., 2026; Gilani et al., 2025).

Untuk mengatasi tantangan tersebut, metode pemetaan otomatis terminologi medis berevolusi dari pendekatan rule-based dan leksikal (transparan tetapi rentan variasi bahasa dan skalabilitas rendah), ke metode berbasis machine learning dan deep learning (lebih baik dalam variasi leksikal tetapi membutuhkan data latih besar dan komputasi intensif), hingga era terkini dengan pemanfaatan Large Language Models (LLM) dan Retrieval-Augmented Generation (RAG) untuk menangani kompleksitas dan variasi data klinis secara lebih cerdas.

Pendekatan rule-based dan leksikal untuk mapping konsep memiliki kelebihan dengan aturannya yang transparan, mudah dilacak, tidak memerlukan data latih yang tinggi dan dengan pola yang tervalidasi dapat menghasilkan akurasi tinggi, tetapi memerlukan waktu dan biaya pengembangan besar, rentan terhadap variasi bahasa (seperti sinonim, singkatan dan ekspresi informal), dan skalabilitas (adaptasi) rendah (Kim, 2014; Meizoso et al., 2011).

Kelemahan rule-based diatasi oleh pendekatan machine learning, tetapi ternyata memerlukan data latih berlabel dalam jumlah cukup dan memiliki ketergantungan pada kualitas fitur (Agrawal, 2018; Januel et al., 2011). Sementara itu, mapping dengan pendekatan deep learning, terutama dengan transformer telah berhasil membuat automatic feature learning, dan dengan NER (Named Entity Recognition) telah mampu menangkap konteks semantik yang kompleks. Akan tetapi pendekatan ini memerlukan data latih yang sangat besar, komputasi intensif (daya komputasi tinggi) dan rentan terhadap bias data (Hristov et al., 2021; Soriano et al., 2019; Zhou et al., 2024).

Meskipun NER merupakan komponen penting dalam pipeline pemrosesan bahasa klinis, ia harus diintegrasikan dengan metode lain seperti semantic similarity matching, knowledge graph retrieval, atau RAG berbasis LLM untuk mencapai pemetaan terminologi yang akurat, terkoneksi, dan siap interoperabilitas. Penelitian terkini pun mengonfirmasi bahwa pendekatan hybrid yang menggabungkan rule-based, NER, dan retrieval semantik memberikan hasil yang lebih robust, khususnya dalam konteks bahasa rendah sumber dan data klinis yang heterogen (Chen et al., 2020; Gilani et al., 2025; Pezoulas et al., 2021).

Beberapa penelitian juga telah dilakukan dengan kombinasi pendekatan yang telah disebutkan sebelumnya. Salah satunya adalah penelitian yang menunjukkan keunggulan mapping berbasis ontologi (gabungan graph dan deep learning mapping terms ke konsep embeddings SNOMED CT) untuk akurasi semantik dan menunjukkan hasil yang lebih baik dari corpus-based untuk similarity & normalization (Zahra & Kate, 2024).

Penelitian lain dilakukan dengan mengembangkan metode transcoding LOINC yang mempertimbangkan hierarki dan korelasi antar komponen kode LOINC. Penelitian tersebut bukan hanya berupa klasifikasi multi-label sederhana, tetapi juga untuk meningkatkan akurasi dan efisiensi, sebagai alternatif hemat biaya bagi model bahasa yang sangat baik (Michel-Picque et al., 2024).

Di sisi lain, tren penggunaan LLM juga mempengaruhi metode untuk mapping terminologi klinis. Evaluasi teknik prompt engineering pada LLM standar, fine-tuning, dan Retrieval-Augmented Generation (RAG) telah dilakukan untuk meningkatkan akurasi mapping terminology medis lokal ke SNOMED CT. Hasilnya menunjukkan bahwa GPT-4 terutama dengan RAG, jauh lebih baik dari baseline LLM biasa, dan relevan untuk rumah sakit di negara non-Inggris seperti Korea (Huh, 2025). Meskipun demikian, masih terdapat kendala dalam specificity (misalnya, mapping terlalu umum). Penelitian tersebut menekankan potensi AI-human collaboration untuk standarisasi data kesehatan, dengan saran penelitian lanjutan untuk refine specificity dan validasi klinis.

Penelitian terkini menunjukkan bahwa pendekatan hibrida yang menggabungkan rule-based, NER, dan retrieval semantik memberikan hasil lebih robust, terutama untuk bahasa dengan sumber daya rendah dan data klinis heterogen (Chen et al., 2020; Gilani et al., 2025; Pezoulas et al., 2021). Salah satu terobosan penting adalah CDE-Mapper (Gilani et al., 2025\) yang menggunakan LLM dan RAG untuk memetakan Clinical Data Elements (CDE) ke beberapa controlled vocabularies (SNOMED CT, LOINC, ICD-10, dll.). Hasil penelitiannya terbukti lebih unggul dari metode baseline, terutama untuk CDE composite. Namun, CDE-Mapper memiliki tiga keterbatasan utama yang menjadi celah penelitian (research gap) dan berhubungan langsung dengan kebutuhan konteks Indonesia.

Pertama, meskipun CDE-Mapper mampu memetakan ke banyak standar, mayoritas penelitian pemetaan terminologi klinis masih berfokus pada SNOMED CT saja, padahal interoperabilitas melalui SATUSEHAT menuntut pemetaan simultan ke SNOMED CT, LOINC, dan ICD-10 secara terpadu. Kedua, CDE-Mapper dirancang khusus untuk memproses item data spesifik (CDE) dan tidak dirancang untuk menangani teks panjang (long text) yang menjadi ciri khas dokumen rekam medis seperti catatan dokter, resume kepulangan, atau catatan perawatan. Dokumen semacam itu dapat berisi puluhan entitas klinis dalam kalimat kompleks, sehingga diperlukan integrasi modul long-text entity extraction (NER) berbasis LLM sebelum pemetaan. Ketiga, CDE-Mapper diuji pada teks bahasa Inggris. Untuk dapat diterapkan di Indonesia, seluruh komponen retrieval ensemble perlu disesuaikan dengan karakteristik linguistik bahasa Indonesia, keterbatasan sumber daya terminologi (ketersediaan SNOMED CT dan LOINC dalam bahasa Indonesia masih terbatas), serta variasi istilah lokal yang luas.

Penelitian terkini juga mengonfirmasi bahwa performa model canggih sekalipun dapat menurun secara signifikan saat menghadapi variasi leksikal atau saat diaplikasikan pada data non-Inggris (Gallifant et al., 2024; Michel-Picque et al., 2024; Rouhizadeh et al., 2025). Oleh karena itu, dibutuhkan pendekatan yang lebih efisien, ringan secara komputasi, namun tetap mampu menangani karakteristik linguistik dan terminologi spesifik bahasa Indonesia untuk memetakan istilah klinis lokal ke standar internasional (Gehrmann et al., 2025; Huh, 2025). Situasi ini membuka peluang penelitian untuk mengembangkan solusi pemetaan yang diadaptasi khusus untuk konteks Indonesia sehingga potensi interoperabilitas data kesehatan mencapai potensi penuhnya.

## Rumusan Masalah

Berdasarkan latar belakang, dapat dirumuskan beberapa permasalahan utama dalam pemetaan terminologi klinis untuk konteks interoperabilitas data klinis di Indonesia sebagai berikut.

1. Interoperabilitas data kesehatan menuntut pemetaan otomatis lintas standar. Namun, mayoritas penelitian hanya fokus pada SNOMED CT, sehingga diperlukan pipeline terpadu untuk pemetaan ke SNOMED CT, LOINC, dan ICD-10 secara simultan.  
2. CDE-Mapper (Gilani et al., 2025\) efektif untuk item data spesifik tetapi tidak menangani teks panjang rekam medis. Oleh karena itu, diperlukan integrasi modul *long-text entity extraction* (NER) berbasis LLM untuk memetakan seluruh CDE dari satu dokumen klinis.  
3. CDE-Mapper diuji pada teks Inggris. Agar dapat diterapkan di Indonesia, komponen retrieval ensemble perlu disesuaikan untuk teks klinis bahasa Indonesia mengingat perbedaan linguistik, keterbatasan terminologi, dan variasi istilah lokal.

## Tujuan Penelitian

Penelitian ini bertujuan untuk mengembangkan dan mengevaluasi sebuah framework adaptif untuk pemetaan terminologi klinis Bahasa Indonesia ke kosakata terkendali standar untuk mendukung interoperabilitas. Secara spesifik, tujuan penelitian adalah sebagai berikut.

1. Memodifikasi arsitektur CDE-Mapper agar mampu melakukan pemetaan simultan istilah klinis berbahasa Indonesia ke tiga standar terminologi sekaligus, yaitu SNOMED CT, LOINC, dan ICD-10.  
2. Mengadaptasi CDE-Mapper dengan integrasi modul *long-text entity extraction* (NER) berbasis LLM untuk pengenalan data klinis dari teks panjang.  
3. Membangun dan mengintegrasikan komponen retrieval ensemble dalam arsitektur CDE-Mapper agar mampu memproses teks klinis berbahasa Indonesia.

## Manfaat Penelitian

Penelitian ini diharapkan dapat memberikan kontribusi berupa solusi yang lebih terjangkau dan praktis untuk standardisasi data klinis di Indonesia, mendukung integrasi data, penelitian translasional, dan pada akhirnya meningkatkan pelayanan kesehatan. Manfaat secara teoritis dan praktis adalah sebagai berikut.

### Manfaat Teoritis

1. Memperluas arsitektur RAG klinis ke domain teks panjang, retrieval ensemble untuk bahasa Indonesia, dan pemetaan simultan multi-standar.  
2. Memberikan advancements dalam *transfer learning* untuk *clinical domain* bahasa non-Inggris.  
3. Memberikan kontribusi pada *theoretical framework* untuk *semantic interoperability* dalam healthcare.

### Manfaat Praktis

1. Meningkatkan kualitas dan konsistensi data nasional.  
2. Meningkatkan efisiensi dokumentasi klinis.  
3. Memfasilitasi pertukaran data yang *meaningful* antar fasilitas kesehatan.  
4. Mengurangi beban mapping manual bagi fasilitas kesehatan.  
5. Meningkatkan akurasi *clinical decision support systems*.  
6. Memungkinkan *real-world evidence research* berkualitas tinggi.  
7. Mendukung *clinical trials* dan *observational studies*.  
8. Memfasilitasi *clinical data sharing* untuk *research collaborations*.



## Daftar Referensi

Agrawal, A. (2018). Evaluating lexical similarity and modeling discrepancies in the procedure hierarchy of SNOMED CT. *BMC Medical Informatics and Decision Making*, *18*. https://doi.org/10.1186/S12911-018-0673-Z

Ayuningtyas, N. W., Mufidah, P. K., Yusuf, S., Sitompul, T., & Susanti, M. I. (2025). Bringing Interoperability into Action: Adoption of Health Terminology Standard in Indonesia. *Studies in health technology and informatics*, *329*, 83–87. https://doi.org/10.3233/SHTI250806

Bennett, A. M., Ulrich, H., Damme, P. V., Wiedekopf, J., & Johnson, A. E. W. (2023). MIMIC-IV on FHIR: converting a decade of in-patient data into an exchangeable, interoperable format. *Journal of the American Medical Informatics Association*, *30*(4), 718–725. https://doi.org/10.1093/JAMIA/OCAD002

Bidgood, W. D. (1998). The SNOMED DICOM microglossary: Controlled terminology resource for data interchange in biomedical imaging. *Methods of Information in Medicine*, *37*(4-5), 404–414. https://doi.org/10.1055/s-0038-1634557

Chen, L., Fu, W., Gu, Y., Sun, Z., Li, H., Li, E., Jiang, L., Gao, Y., & Huang, Y. (2020). Clinical concept normalization with a hybrid natural language processing system combining multilevel matching and machine learning ranking. *Journal of the American Medical Informatics Association*, *27*(10), 1576–1584. https://doi.org/10.1093/JAMIA/OCAA155

Chen, Y., Hu, D., Li, M., Duan, H., & Lu, X. (2022). Automatic SNOMED CT coding of Chinese clinical terms via attention-based semantic matching. *International Journal of Medical Informatics*, *159*, 104676. https://doi.org/10.1016/j.ijmedinf.2021.104676

Eslami, B., Dligach, D., Azarvash, N., De La Pena, P., Strickland, B., & Tootooni, S. (2026). A Hybrid Language Framework for Ontology-Based Clinical Concept Extraction. *Journal of Healthcare Informatics Research*. https://doi.org/10.1007/s41666-026-00232-0

Gallifant, J., Chen, S., Moreira, P., Munch, N., Gao, M., Pond, J., Aerts, H., Celi, L. A., Hartvigsen, T., & Bitterman, D. S. (2024). Language Models are Surprisingly Fragile to Drug Names in Biomedical Benchmarks. *EMNLP 2024 - 2024 Conference on Empirical Methods in Natural Language Processing, Findings of EMNLP 2024*, 12448–12465. https://doi.org/10.18653/V1/2024.FINDINGS-EMNLP.726

Gehrmann, J., Dogan, A., Hagelschuer, L., Quakulinski, L., Koy, A., & Beyan, O. (2025). Catnip for MedCAT: Optimizing the Input for Automated SNOMED CT Mapping of Clinical Variables. *Studies in health technology and informatics*, *331*, 142–152. https://doi.org/10.3233/SHTI251390

Gilani, K., Verket, M., Peters, C., Dumontier, M., Rocca, H. P. B. L., & Urovi, V. (2025). CDE-Mapper: Using retrieval-augmented language models for linking clinical data elements to controlled vocabularies. *Computers in Biology and Medicine*, *196*, 110745. https://doi.org/10.1016/j.compbiomed.2025.110745

Heryawan, L., Mori, Y., Yamamoto, G., Kume, N., Lazuardi, L., Fuad, A., & Kuroda, T. (2025). Fast Healthcare Interoperability Resources (FHIR)-Based Interoperability Design in Indonesia: Content Analysis of Developer Hub's Social Networking Service. *JMIR formative research*, *9*, e51270. https://doi.org/10.2196/51270

Hossain, M. K., Sutanto, J., Handayani, P. W., Haryanto, A. A., Bhowmik, J., & Frings-Hessami, V. (2025). An exploratory study of electronic medical record implementation and recordkeeping culture: the case of hospitals in Indonesia. *BMC Health Services Research*, *25*(1), 249. https://doi.org/10.1186/s12913-025-12399-0

Hristov, A., Tahchiev, A., Papazov, H., Tulechki, N., Primov, T., & Boytcheva, S. (2021). Application of Deep Learning Methods to SNOMED CT Encoding of Clinical Texts: From Data Collection to Extreme Multi-Label Text-Based Classification. *International Conference Recent Advances in Natural Language Processing, RANLP*, 557–565. https://doi.org/10.26615/978-954-452-072-4_063

Huh, S. (2025). Comparative Analysis of ChatGPT-4 for Automated Mapping of Local Medical Terminologies to SNOMED CT. *Studies in Health Technology and Informatics*, *327*, 813–817. https://doi.org/10.3233/SHTI250472

Januel, J. M., Luthi, J. C., Quan, H., Borst, F., Taffé, P., Ghali, W. A., & Burnand, B. (2011). Improved accuracy of co-morbidity coding over time after the introduction of ICD-10 administrative data. *BMC Health Services Research*, *11*. https://doi.org/10.1186/1472-6963-11-194

Kate, R. J. (2020). Automatic full conversion of clinical terms into SNOMED CT concepts. *Journal of Biomedical Informatics*, *111*. https://doi.org/10.1016/j.jbi.2020.103585

Kim, T. Y. (2014). Automating lexical cross-mapping of ICNP to SNOMED CT. *Informatics for Health and Social Care*, *41*(1), 64–77. https://doi.org/10.3109/17538157.2014.948173

Meizoso, M., Allones, J. L., Taboada, M., Martinez, D., & Tellado, S. (2011). Automated Mapping of Observation Archetypes to SNOMED CT Concepts. *Lecture Notes in Computer Science (including subseries Lecture Notes in Artificial Intelligence and Lecture Notes in Bioinformatics)*, *6686 LNCS*(PART 1), 550–561. https://doi.org/10.1007/978-3-642-21344-1_57

Michel-Picque, T., Bringay, S., Poncelet, P., Patel, N., & Mayoral, G. (2024). Classifier chains for LOINC transcoding. *Studies in Health Technology and Informatics*, *316*, 1314–1318. https://doi.org/10.3233/SHTI240654

Park, Y., Kang, H., Kim, J., Shin, S. Y., Cho, D., Rhee, S. Y., Park, H. S., Lee, K. J., & Bae, S. (2026). Development and Evaluation of SNOMED CT Automated Mapping Tool: Advancing Terminology Standardization and Semantic Interoperability. *JMIR Medical Informatics*, *14*, e82670. https://doi.org/10.2196/82670

Peterson, K. J., & Liu, H. (2020). Automating the Transformation of Free-Text Clinical Problems into SNOMED CT Expressions. *AMIA Joint Summits on Translational Science proceedings. AMIA Joint Summits on Translational Science*, *2020*, 497–506.

Pezoulas, V. C., Sakellarios, A., Kleber, M., Bosch, J. A., Laan, S. W. V. D., Lamers, F., Lehtimäki, T., März, W., & Fotiadis, D. I. (2021). A hybrid data harmonization workflow using word embeddings for the interlinking of heterogeneous cross-domain clinical data structures. *BHI 2021 - 2021 IEEE EMBS International Conference on Biomedical and Health Informatics, Proceedings*. https://doi.org/10.1109/BHI50953.2021.9508484

Rinaldi, E., Drenkhahn, C., Gebel, B., Saleh, K., Tönnies, H., Loewenich, F. D. V., Thoma, N., Baier, C., Boeker, M., Hinske, L. C., Diaz, L. A. P., Behnke, M., Ingenerf, J., & Thun, S. (2023). Towards interoperability in infection control: a standard data model for microbiology. *Scientific Data*, *10*(1). https://doi.org/10.1038/S41597-023-02560-X

Rouhizadeh, H., Yazdani, A., Zhang, B., Alvarez, D. V., Hüser, M., Vanobberghen, A., Yang, R., Li, I., Walter, A., & Teodoro, D. (2025). Large Language Models Struggle to Encode Medical Concepts — A Multilingual Benchmarking and Comparative Analysis. *medRxiv*. https://doi.org/10.1101/2025.01.15.25320579

Sathappan, S. M. K., Jeon, Y. S., Dang, T. K., Lim, S. C., Shao, Y. M., Tai, E. S., & Feng, M. (2021). Transformation of Electronic Health Records and Questionnaire Data to OMOP CDM: A Feasibility Study Using sgt2dm Dataset. *Applied Clinical Informatics*, *12*(4), 757–767. https://doi.org/10.1055/S-0041-1732301

Soriano, I. M., Pena, J. L. C., Breis, J. T. F., Roman, I. S., Barriuso, A. A., & Baraza, D. G. (2019). Snomed2Vec: Representation of SNOMED CT terms with Word2Vec. *Proceedings - IEEE Symposium on Computer-Based Medical Systems*, *2019-June*, 678–683. https://doi.org/10.1109/CBMS.2019.00138

Sugiarto, P., Purnami, C. T., & Jati, S. P. (2024). Supporting and Inhibiting Factors in Implementing Electronic Medical Records (EMR) Policy in Indonesia. *BIO Web of Conferences*, *133*, 00038. https://doi.org/10.1051/bioconf/202413300038

Yu, S., Cho, E. J., Kim, S., Park, K., Kim, M. S., Oh, Y., & Ryu, H. (2026). Large Language Models’ Performances regarding logical observation identifiers names and codes mapping in laboratory medicine: A comparative analysis of ChatGPT-4.0, Gemini, and Perplexity. *International Journal of Medical Informatics*, *209*, 106270. https://doi.org/10.1016/j.ijmedinf.2026.106270

Zahra, F. A., & Kate, R. J. (2024). Obtaining clinical term embeddings from SNOMED CT ontology. *Journal of Biomedical Informatics*, *149*. https://doi.org/10.1016/j.jbi.2023.104560

Zhou, X., Dhingra, L. S., Aminorroaya, A., Adejumo, P., & Khera, R. (2024). A Novel Sentence Transformer-based Natural Language Processing Approach for Schema Mapping of Electronic Health Records to the OMOP Common Data Model. *AMIA ... Annual Symposium proceedings. AMIA Symposium*, *2024*, 1332–1339.