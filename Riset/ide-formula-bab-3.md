# Ide Penambahan Formula Matematika pada Subbab 3.3 dan 3.4

## Tujuan

Formula matematika sebaiknya digunakan untuk memformalkan proses yang saat ini masih dijelaskan secara naratif, terutama:

1. hubungan antara *retriever* dan generator dalam RAG;
2. pembentukan kandidat melalui *sparse* dan *dense retrieval*;
3. penggabungan hasil kedua *retriever*;
4. penyaringan kandidat berdasarkan metadata dan ambang kemiripan;
5. *ranking* dan *reranking* berbasis LLM;
6. pengukuran konsistensi hasil penilaian LLM; dan
7. pemilihan kode akhir atau keputusan untuk tidak memetakan istilah.

Formula proses tersebut cocok ditempatkan pada Subbab 3.3 dan 3.4. Formula evaluasi seperti *Recall@k* dan MRR tetap ditempatkan pada bagian metrik evaluasi agar tidak terjadi pengulangan.

---

## A. Usulan Formula untuk Subbab 3.3: Retrieval-Augmented Generation

### 1. Formulasi probabilistik RAG

**Lokasi yang disarankan:** setelah paragraf pembuka Subbab 3.3 yang menjelaskan penggabungan *retrieval* dan *generation*.

Untuk masukan atau kueri $q$, *retriever* mengambil himpunan konteks atau dokumen kandidat $Z_k(q)$. Probabilitas keluaran $y$ dapat dirumuskan sebagai:

$$
p(y \mid q)
=
\sum_{z \in Z_k(q)}
p_{\eta}(z \mid q)\,
p_{\theta}(y \mid q,z),
$$

dengan:

- $q$ adalah kueri atau istilah klinis;
- $z$ adalah konsep atau dokumen terminologi yang diambil;
- $Z_k(q)$ adalah $k$ kandidat teratas;
- $p_{\eta}(z \mid q)$ adalah probabilitas kandidat menurut *retriever*; dan
- $p_{\theta}(y \mid q,z)$ adalah probabilitas keluaran menurut generator dengan mempertimbangkan kandidat $z$.

Formula ini memperjelas bahwa keluaran RAG bergantung pada dua komponen: kualitas kandidat yang ditemukan dan kemampuan generator menggunakan kandidat tersebut.

### 2. Distribusi probabilitas kandidat retrieval

Skor kandidat dapat diubah menjadi probabilitas menggunakan fungsi *softmax*:

$$
p_{\eta}(z_i \mid q)
=
\frac{\exp(s(q,z_i))}
{\sum_{z_j \in Z_k(q)}\exp(s(q,z_j))},
$$

di mana $s(q,z_i)$ adalah skor relevansi antara kueri $q$ dan kandidat $z_i$.

Formula ini dapat ditempatkan setelah pembahasan *top-k documents* pada bagian Arsitektur RAG.

### 3. Skor dense retrieval

**Lokasi yang disarankan:** setelah penjelasan bahwa kueri dan dokumen diubah menjadi representasi vektor.

Untuk *dense retriever*, kemiripan kueri dan kandidat dapat dihitung dengan *cosine similarity*:

$$
s_{\mathrm{dense}}(q,c)
=
\frac{\mathbf{e}_q^{\top}\mathbf{e}_c}
{\lVert\mathbf{e}_q\rVert_2\lVert\mathbf{e}_c\rVert_2},
$$

dengan $\mathbf{e}_q$ sebagai vektor embedding kueri dan $\mathbf{e}_c$ sebagai vektor embedding kandidat konsep.

Dalam konteks terminologi klinis, formula ini sesuai untuk menjelaskan cara SapBERT mendekatkan istilah yang berbeda secara leksikal tetapi memiliki makna klinis serupa.

### 4. Skor sparse retrieval

Untuk *sparse retriever* seperti SPLADE, kueri dan kandidat direpresentasikan sebagai vektor berbobot pada ruang kosakata. Skornya dapat dituliskan sebagai:

$$
s_{\mathrm{sparse}}(q,c)
=
\mathbf{w}_q^{\top}\mathbf{w}_c
=
\sum_{t \in V}w_{q,t}w_{c,t},
$$

dengan:

- $V$ adalah kosakata;
- $w_{q,t}$ adalah bobot token $t$ pada kueri; dan
- $w_{c,t}$ adalah bobot token $t$ pada kandidat.

Formula ini menunjukkan peran SPLADE dalam mempertahankan kecocokan istilah, singkatan, atau token klinis yang penting.

### 5. Pembentukan himpunan top-k kandidat

Proses pemilihan kandidat dapat diformalkan sebagai:

$$
C_k(q)
=
\underset{C \subseteq \mathcal{K},\,|C|=k}{\operatorname{arg\,max}}
\sum_{c \in C}s(q,c),
$$

di mana $\mathcal{K}$ adalah seluruh konsep dalam basis pengetahuan dan $C_k(q)$ merupakan himpunan $k$ kandidat dengan skor tertinggi.

Versi yang lebih sederhana untuk naskah adalah:

$$
C_k(q)=\operatorname{TopK}_{c\in\mathcal{K}}s(q,c).
$$

### 6. Hybrid retrieval berbasis weighted score

**Lokasi yang disarankan:** pada pembahasan *Advanced RAG* yang menyebut penggabungan BM25/*sparse retrieval* dengan *dense embedding*.

Setelah kedua skor dinormalisasi, skor gabungan dapat dirumuskan sebagai:

$$
s_{\mathrm{hybrid}}(q,c)
=
\alpha\,\widetilde{s}_{\mathrm{sparse}}(q,c)
+
(1-\alpha)\,\widetilde{s}_{\mathrm{dense}}(q,c),
$$

dengan $0\leq\alpha\leq1$. Parameter $\alpha$ mengatur kontribusi kecocokan leksikal dan semantik.

Untuk data klinis Bahasa Indonesia, nilai $\alpha$ dapat ditentukan melalui validasi. Nilai yang lebih tinggi memberi bobot lebih besar pada kecocokan istilah, sedangkan nilai yang lebih rendah memberi bobot lebih besar pada kesamaan semantik.

### 7. Alternatif penggabungan dengan Reciprocal Rank Fusion

Apabila skor SPLADE dan SapBERT tidak berada pada skala yang sebanding, *Reciprocal Rank Fusion* (RRF) lebih aman digunakan:

$$
s_{\mathrm{RRF}}(c)
=
\sum_{m=1}^{M}
\frac{1}{k_0+r_m(c)},
$$

dengan:

- $M$ adalah jumlah *retriever*;
- $r_m(c)$ adalah posisi kandidat $c$ pada hasil *retriever* ke-$m$; dan
- $k_0$ adalah konstanta untuk mengurangi dominasi kandidat pada peringkat pertama.

RRF cocok untuk menggabungkan SPLADE dan SapBERT karena menggunakan posisi kandidat, bukan nilai skor mentah.

---

## B. Usulan Formula untuk Subbab 3.4: Implementasi RAG dan LLM dalam CDE-Mapper

### 1. Dekomposisi kueri komposit

**Lokasi yang disarankan:** setelah paragraf tentang *query decomposition*.

Kueri klinis komposit $q$ dapat direpresentasikan sebagai himpunan subkueri:

$$
\mathcal{Q}(q)
=
\{q_0,q_1,\ldots,q_m\},
$$

dengan $q_0$ sebagai *base entity* dan $q_1,\ldots,q_m$ sebagai atribut atau entitas terkait.

Kandidat gabungan dari seluruh subkueri dapat dirumuskan sebagai:

$$
C(q)
=
\bigcup_{j=0}^{m} C_k(q_j).
$$

Formula ini menjelaskan bahwa kandidat untuk CDE komposit tidak hanya diperoleh dari frasa utuh, tetapi dari setiap komponen semantiknya.

### 2. Ensemble retrieval SPLADE dan SapBERT

**Lokasi yang disarankan:** setelah penjelasan komponen ketiga, yaitu *knowledge retrieval*.

Untuk setiap subkueri $q_j$, skor kandidat dapat dirumuskan sebagai:

$$
s_{\mathrm{ret}}(q_j,c)
=
\alpha\,\widetilde{s}_{\mathrm{SPLADE}}(q_j,c)
+
(1-\alpha)\,\widetilde{s}_{\mathrm{SapBERT}}(q_j,c).
$$

Jika satu kandidat muncul pada beberapa subkueri, skor agregatnya dapat dihitung sebagai:

$$
s_{\mathrm{agg}}(q,c)
=
\sum_{j=0}^{m}\omega_j s_{\mathrm{ret}}(q_j,c),
\qquad
\sum_{j=0}^{m}\omega_j=1,
$$

dengan $\omega_j$ sebagai bobot kepentingan subkueri. *Base entity* dapat diberi bobot lebih besar daripada atribut tambahan.

### 3. Metadata filtering dan similarity threshold

**Lokasi yang disarankan:** setelah penjelasan komponen keempat, yaitu *knowledge filtering*.

Himpunan kandidat setelah penyaringan dapat didefinisikan sebagai:

$$
C'(q)
=
\left\{
c\in C(q)
\;\middle|\;
s_{\mathrm{agg}}(q,c)\geq\tau
\land
d(c)=d(q)
\right\},
$$

dengan:

- $\tau$ adalah ambang minimum kemiripan;
- $d(q)$ adalah domain klinis kueri; dan
- $d(c)$ adalah domain terminologi kandidat.

Jika kecocokan domain tidak harus biner, kesesuaian metadata dapat dinyatakan sebagai:

$$
m(q,c)\in[0,1],
$$

kemudian dimasukkan ke skor kandidat:

$$
s_{\mathrm{filter}}(q,c)
=
s_{\mathrm{agg}}(q,c)+\lambda_m m(q,c).
$$

### 4. Skor reranking berbasis beberapa aspek klinis

**Lokasi yang disarankan:** pada awal penjelasan komponen kelima, yaitu *two-step reranking*.

Penilaian LLM sebaiknya tidak hanya menghasilkan satu skor umum, tetapi dapat dibangun dari beberapa aspek:

$$
s_{\mathrm{LLM}}(q,c)
=
\beta_1 s_{\mathrm{semantic}}
+\beta_2 s_{\mathrm{domain}}
+\beta_3 s_{\mathrm{attribute}}
+\beta_4 s_{\mathrm{granularity}},
$$

dengan:

$$
\sum_{r=1}^{4}\beta_r=1.
$$

Komponen skor tersebut dapat diartikan sebagai:

- $s_{\mathrm{semantic}}$: kesesuaian makna utama;
- $s_{\mathrm{domain}}$: kesesuaian terminologi target;
- $s_{\mathrm{attribute}}$: kelengkapan atribut seperti lokasi, metode, unit, dan tingkat keparahan; serta
- $s_{\mathrm{granularity}}$: kecocokan tingkat kekhususan konsep.

Formula ini sangat relevan untuk membedakan kandidat yang secara leksikal mirip tetapi terlalu umum atau berasal dari domain yang tidak tepat.

### 5. Penggabungan skor retrieval dan reranking

Skor akhir kandidat dapat menggabungkan bukti dari *retriever* dan penilaian LLM:

$$
s_{\mathrm{final}}(q,c)
=
\gamma\,\widetilde{s}_{\mathrm{filter}}(q,c)
+
(1-\gamma)\,s_{\mathrm{LLM}}(q,c),
$$

dengan $0\leq\gamma\leq1$.

Formula ini menjaga agar keputusan akhir tidak sepenuhnya bergantung pada LLM. Kandidat tetap harus memiliki dukungan retrieval yang memadai.

### 6. Kategori relevansi pada two-step reranking

Kategori tahap kedua dapat ditentukan dari skor reranking:

$$
L(q,c)=
\begin{cases}
\textit{exact match}, & s_{\mathrm{final}}\geq\tau_3,\\
\textit{highly relevant}, & \tau_2\leq s_{\mathrm{final}}<\tau_3,\\
\textit{partially relevant}, & \tau_1\leq s_{\mathrm{final}}<\tau_2,\\
\textit{not relevant}, & s_{\mathrm{final}}<\tau_1.
\end{cases}
$$

Nilai $\tau_1$, $\tau_2$, dan $\tau_3$ perlu ditentukan menggunakan data validasi dan penilaian ahli klinis.

### 7. Self-consistency pada reranking LLM

**Lokasi yang disarankan:** setelah kalimat yang menjelaskan bahwa penilaian diulang beberapa kali menggunakan prompt yang sama.

Jika penilaian dilakukan sebanyak $T$ kali, rerata skor kandidat adalah:

$$
\overline{s}_{\mathrm{LLM}}(q,c)
=
\frac{1}{T}\sum_{t=1}^{T}s_{\mathrm{LLM}}^{(t)}(q,c).
$$

Variabilitas skor dapat dihitung sebagai:

$$
\sigma^2(q,c)
=
\frac{1}{T}\sum_{t=1}^{T}
\left(s_{\mathrm{LLM}}^{(t)}(q,c)-\overline{s}_{\mathrm{LLM}}(q,c)\right)^2.
$$

Untuk keluaran kategorikal, *confidence score* dapat dirumuskan sebagai proporsi label mayoritas:

$$
\operatorname{Conf}(q,c)
=
\max_{\ell\in\mathcal{L}}
\frac{1}{T}
\sum_{t=1}^{T}
\mathbb{1}\!\left(L^{(t)}(q,c)=\ell\right),
$$

dengan $\mathcal{L}$ sebagai himpunan kategori relevansi.

Kandidat hanya diterima jika:

$$
\operatorname{Conf}(q,c)\geq\delta.
$$

Formula ini merupakan representasi matematis langsung dari mekanisme *self-consistency* yang sudah dijelaskan pada naskah.

### 8. Pemilihan kode akhir dan mekanisme abstain

Kandidat akhir dipilih berdasarkan skor tertinggi:

$$
c^*
=
\underset{c\in C'(q)}{\operatorname{arg\,max}}
\;s_{\mathrm{final}}(q,c).
$$

Namun, untuk mengurangi pemetaan yang dipaksakan, sistem sebaiknya memiliki mekanisme *abstain*:

$$
\widehat{c}(q)=
\begin{cases}
c^*, & s_{\mathrm{final}}(q,c^*)\geq\tau_{\mathrm{accept}}
\land \operatorname{Conf}(q,c^*)\geq\delta,\\
\varnothing, & \text{selainnya}.
\end{cases}
$$

Nilai $\varnothing$ menunjukkan bahwa sistem tidak menemukan kandidat yang cukup meyakinkan dan kasus perlu ditinjau oleh ahli.

### 9. Pemetaan CDE komposit

Untuk CDE komposit, hasil pemetaan dapat berupa beberapa konsep $M=\{c_0,c_1,\ldots,c_m\}$. Skor satu konfigurasi pemetaan dapat dirumuskan sebagai:

$$
S(M\mid q)
=
\sum_{j=0}^{m}\omega_j s_{\mathrm{final}}(q_j,c_j)
-
\lambda\,P_{\mathrm{inconsistent}}(M),
$$

dengan $P_{\mathrm{inconsistent}}(M)$ sebagai penalti jika kombinasi konsep memiliki domain, atribut, atau relasi yang tidak konsisten.

Konfigurasi terbaik adalah:

$$
M^*=\underset{M}{\operatorname{arg\,max}}\;S(M\mid q).
$$

Formula ini dapat menjadi penghubung teoritis antara *query decomposition*, retrieval per subkueri, dan penyusunan kembali representasi konsep komposit.

### 10. Formula terpadu yang khas untuk penelitian

Jika hanya satu formula utama yang akan digunakan untuk merangkum adaptasi CDE-Mapper dalam penelitian ini, skor akhir kandidat dapat dirumuskan sebagai:

$$
S_{\mathrm{akhir}}(q,c)
=
w_l S_{\mathrm{leksikal}}(q,c)
+w_s S_{\mathrm{semantik}}(q,c)
+w_d S_{\mathrm{domain}}(q,c)
+w_a S_{\mathrm{atribut}}(q,c)
+w_g S_{\mathrm{granularitas}}(q,c)
+w_k S_{\mathrm{konsistensi}}(q,c),
$$

dengan ketentuan:

$$
w_l+w_s+w_d+w_a+w_g+w_k=1,
\qquad
w_i\geq0.
$$

Setiap komponen memiliki fungsi sebagai berikut:

- $S_{\mathrm{leksikal}}$ mengukur kesamaan kata, ejaan, singkatan, dan token penting antara istilah klinis dengan kandidat. Nilainya dapat berasal dari SPLADE.
- $S_{\mathrm{semantik}}$ mengukur kesamaan makna meskipun istilah sumber dan kandidat menggunakan susunan kata atau bahasa yang berbeda. Nilainya dapat berasal dari SapBERT atau model embedding biomedis.
- $S_{\mathrm{domain}}$ mengukur kesesuaian jenis entitas dengan terminologi target, misalnya observasi laboratorium dengan LOINC serta kondisi klinis dengan SNOMED CT atau ICD.
- $S_{\mathrm{atribut}}$ mengukur kelengkapan pemetaan atribut, seperti lokasi anatomis, metode pemeriksaan, satuan, posisi tubuh, waktu pengukuran, dan tingkat keparahan.
- $S_{\mathrm{granularitas}}$ mengukur kesesuaian tingkat kekhususan kandidat agar sistem tidak memilih konsep yang terlalu umum atau terlalu spesifik.
- $S_{\mathrm{konsistensi}}$ mengukur kestabilan keputusan LLM ketika proses penilaian atau *reranking* diulang beberapa kali.

Kandidat terbaik kemudian dipilih menggunakan:

$$
c^*
=
\underset{c\in C'(q)}{\operatorname{arg\,max}}
\;S_{\mathrm{akhir}}(q,c).
$$

Apabila nilai tertinggi masih berada di bawah ambang penerimaan, sistem tidak perlu memaksakan pemetaan dan dapat mengirimkan kasus tersebut untuk validasi ahli klinis.

Formula ini merupakan bentuk ringkas dari keseluruhan proses. Skor leksikal dan semantik berasal dari tahap *retrieval*, skor domain dan atribut berasal dari *filtering* serta aturan pengaitan, sedangkan skor granularitas dan konsistensi diperkuat pada tahap *reranking* berbasis LLM. Dengan demikian, formula ini menghubungkan RAG umum dengan kebutuhan khusus pemetaan terminologi klinis Bahasa Indonesia.

**Lokasi penyisipan yang direkomendasikan dalam `bab-3.tex`:** Subbab 3.4.1 *Framework CDE-Mapper Gilani*, setelah paragraf komponen kelima tentang *two-step reranking* dan sebelum paragraf komponen keenam tentang *knowledge reservoir integration*. Jika diperlukan judul tambahan, bagian tersebut dapat diberi judul:

```latex
\subsubsection{Formalisasi Skor Akhir Kandidat}
```

Urutan pembahasannya menjadi:

1. *knowledge retrieval* menghasilkan kandidat dan skor awal;
2. *knowledge filtering* membuang kandidat yang tidak relevan;
3. *two-step reranking* menilai kesesuaian klinis kandidat;
4. formula terpadu menghitung skor akhir dan memilih kandidat terbaik;
5. kandidat dengan skor rendah diarahkan untuk validasi ahli; dan
6. hasil yang telah tervalidasi dimasukkan ke *knowledge reservoir*.

---

## C. Formula yang Paling Diprioritaskan

Jika penambahan formula ingin dibuat ringkas, lima formula berikut paling penting:

| Prioritas | Formula | Bagian penempatan | Alasan |
|---|---|---|---|
| 1 | Skor akhir terpadu enam komponen | Subbab 3.4.1, setelah *two-step reranking* dan sebelum *knowledge reservoir* | Menjadi formula utama yang menghubungkan retrieval, filtering, dan reranking untuk konteks Indonesia |
| 2 | Skor *hybrid retrieval* SPLADE–SapBERT | Subbab 3.4, komponen *knowledge retrieval* | Memformalkan inti retrieval CDE-Mapper |
| 3 | Himpunan kandidat setelah metadata dan threshold filtering | Subbab 3.4, komponen *knowledge filtering* | Memformalkan kandidat yang boleh masuk reranker |
| 4 | Confidence berbasis *self-consistency* | Subbab 3.4, setelah pembahasan pengulangan prompt | Langsung sesuai dengan proses yang telah dijelaskan |
| 5 | Pemilihan kode akhir dengan mekanisme *abstain* | Akhir pembahasan reranking | Penting untuk keselamatan dan validasi ahli |

Formula probabilistik RAG, *cosine similarity*, dan RRF dapat ditambahkan sebagai landasan umum di Subbab 3.3 apabila pembahasan matematis ingin dibuat lebih lengkap.

---

## D. Catatan Konsistensi dengan Bagian Metrik Evaluasi

Pada bagian metrik yang sudah ada, formula *Top-k Accuracy* dan *Recall@k* saat ini identik. Hal tersebut benar hanya pada kasus *single-label* dengan tepat satu konsep relevan untuk setiap kueri. Jika satu entitas dapat memiliki lebih dari satu konsep relevan, *Recall@k* sebaiknya ditulis sebagai:

$$
\operatorname{Recall@}k
=
\frac{1}{N}
\sum_{i=1}^{N}
\frac{|R_i\cap C_i^{(k)}|}{|R_i|},
$$

dengan $R_i$ sebagai himpunan seluruh konsep relevan untuk kasus ke-$i$ dan $C_i^{(k)}$ sebagai kandidat $k$ teratas.

Dengan demikian:

- Subbab 3.3 menjelaskan matematika arsitektur RAG dan retrieval;
- Subbab 3.4 menjelaskan matematika proses CDE-Mapper, filtering, ranking, dan reranking; serta
- bagian metrik menjelaskan cara mengukur keberhasilan proses tersebut.

---

## E. Rekomendasi Akhir

Penambahan formula sebaiknya tidak membuat Bab III terlihat seperti bab metode implementasi. Karena Bab III merupakan landasan teori, parameter seperti $\alpha$, $\gamma$, $\tau$, dan $\delta$ cukup didefinisikan secara konseptual. Nilai aktual, prosedur pencarian parameter, serta eksperimen *ablation* lebih tepat dijelaskan pada bab metodologi.

Formula paling khas untuk penelitian ini adalah formula skor akhir yang menggabungkan kecocokan leksikal, kesamaan semantik, kesesuaian domain terminologi, kelengkapan atribut, tingkat *granularity*, dan konsistensi penilaian LLM. Formula tersebut sebaiknya ditempatkan pada Subbab 3.4.1, setelah penjelasan *two-step reranking* dan sebelum *knowledge reservoir integration*. Posisi ini menunjukkan bahwa formula digunakan setelah kandidat diperoleh dan disaring, tetapi sebelum hasil tervalidasi disimpan ke basis pengetahuan.

Formula terpadu tersebut dapat menjadi dasar matematis yang menghubungkan RAG umum dengan adaptasi CDE-Mapper untuk terminologi klinis Bahasa Indonesia. Sementara itu, formula yang lebih teknis—seperti skor SPLADE, kemiripan SapBERT, RRF, dan ambang filtering—berfungsi menjelaskan komponen-komponen yang membentuk skor akhir tersebut.

---

## F. Penyesuaian yang Diperlukan pada Bab II dan Bab IV

Penambahan formula pada Bab III memiliki konsekuensi terhadap konsistensi antarbab. Akan tetapi, tingkat penyesuaian pada Bab II dan Bab IV berbeda karena masing-masing bab memiliki fungsi yang berbeda. Bab II berfungsi membangun argumentasi berdasarkan penelitian terdahulu dan menunjukkan kesenjangan penelitian, sedangkan Bab IV menjelaskan bagaimana formula tersebut diterapkan dan diuji dalam metode penelitian.

### 1. Penyesuaian pada Bab II: Tinjauan Pustaka

Bab II tidak perlu memuat ulang formula matematika karena formula tersebut merupakan bagian dari landasan teori pada Bab III. Pembahasan Bab II yang sudah menjelaskan *ensemble retrieval*, SPLADE, SapBERT, *knowledge filtering*, *two-step reranking*, dan *self-consistency* pada CDE-Mapper pada dasarnya telah menyediakan latar belakang yang sesuai.

Penyesuaian Bab II hanya diperlukan apabila formula skor akhir terpadu diposisikan sebagai salah satu kontribusi penelitian. Dalam keadaan tersebut, bagian identifikasi kesenjangan penelitian perlu menegaskan bahwa pendekatan sebelumnya belum menyediakan mekanisme penilaian terpadu yang secara eksplisit:

1. menggabungkan kecocokan leksikal dan kesamaan semantik;
2. mempertimbangkan kesesuaian domain terminologi;
3. mengukur kelengkapan atribut klinis;
4. mempertimbangkan tingkat *granularity* kandidat;
5. memasukkan konsistensi penilaian LLM; dan
6. disesuaikan dengan variasi terminologi klinis Bahasa Indonesia.

Penguatan tersebut dapat ditempatkan pada bagian *gap metodologis* dan ringkasan posisi penelitian. Narasi yang disarankan secara konseptual adalah bahwa penelitian tidak hanya menambahkan modul pemrosesan Bahasa Indonesia, tetapi juga mengembangkan mekanisme pemilihan kandidat yang lebih transparan dan terukur melalui skor multi-komponen.

Jika formula hanya dimaksudkan sebagai representasi matematis dari proses CDE-Mapper yang sudah ada, bukan sebagai algoritma baru, Bab II tidak membutuhkan perubahan substantif. Dalam hal ini, formula cukup diperlakukan sebagai sintesis konseptual pada Bab III.

### 2. Penyesuaian pada Bab IV: Metode Penelitian

Bab IV memerlukan penyesuaian yang lebih substantif karena harus menjelaskan bagaimana formula dihitung, dikonfigurasi, dan dievaluasi. Formula tidak perlu ditulis ulang secara lengkap; Bab IV dapat merujuk label persamaan yang tersedia pada Bab III. Namun, seluruh komponennya harus memiliki definisi operasional yang jelas.

#### a. Definisi operasional setiap komponen skor

Bab IV perlu menjelaskan asal nilai setiap komponen:

- $S_{\mathrm{leksikal}}$ diperoleh dari skor SPLADE atau *sparse retriever*;
- $S_{\mathrm{semantik}}$ diperoleh dari kemiripan embedding SapBERT atau *dense retriever*;
- $S_{\mathrm{domain}}$ diperoleh dari kecocokan antara tipe entitas, terminologi target, dan metadata kandidat;
- $S_{\mathrm{atribut}}$ diperoleh dari proporsi atribut hasil dekomposisi yang ditemukan pada kandidat;
- $S_{\mathrm{granularitas}}$ diperoleh dari kesesuaian tingkat kekhususan kandidat terhadap istilah sumber; dan
- $S_{\mathrm{konsistensi}}$ diperoleh dari kestabilan skor atau label dalam beberapa pengulangan reranking LLM.

Tanpa definisi operasional tersebut, formula hanya menjadi penjelasan konseptual dan belum dapat direplikasi dalam eksperimen.

#### b. Normalisasi skor

Skor yang berasal dari model berbeda kemungkinan memiliki rentang yang berbeda. Karena itu, seluruh skor perlu dinormalisasi ke skala yang sama, misalnya $[0,1]$, sebelum digabungkan. Salah satu pilihan adalah normalisasi *min-max*:

$$
\widetilde{S}_j(q,c)
=
\frac{S_j(q,c)-S_j^{\min}}
{S_j^{\max}-S_j^{\min}+\varepsilon},
$$

dengan $\varepsilon$ sebagai konstanta kecil untuk mencegah pembagian dengan nol.

Bab IV harus menjelaskan apakah normalisasi dilakukan per kueri, per kelompok kandidat, atau menggunakan statistik dari data pengembangan.

#### c. Penentuan bobot

Bobot $w_l,w_s,w_d,w_a,w_g,$ dan $w_k$ tidak boleh ditentukan tanpa prosedur yang jelas. Alternatif yang dapat digunakan antara lain:

1. bobot sama sebagai konfigurasi awal;
2. *grid search* pada data pengembangan;
3. optimasi berdasarkan Accuracy@1, MRR, atau metrik utama lain;
4. pembobotan berdasarkan penilaian ahli; atau
5. model pembelajaran sederhana yang mempelajari bobot dari data berlabel.

Proses pemilihan bobot hanya boleh menggunakan data pengembangan atau validasi. Data uji tidak boleh digunakan untuk menentukan bobot agar tidak terjadi kebocoran data.

#### d. Penentuan threshold dan mekanisme abstain

Bab IV perlu menetapkan ambang penerimaan $\tau_{\mathrm{accept}}$ dan ambang konsistensi $\delta$. Kandidat hanya diterima apabila skor akhir dan tingkat konsistensinya memenuhi kedua ambang tersebut. Jika tidak, sistem menghasilkan keputusan *abstain* dan mengirimkan kasus untuk validasi ahli.

Mekanisme ini penting untuk membedakan dua kondisi:

- sistem menemukan kandidat dengan tingkat keyakinan yang memadai; dan
- sistem tidak memiliki bukti yang cukup untuk menghasilkan pemetaan otomatis.

Dengan demikian, nilai *coverage* dapat menurun ketika ambang diperketat, tetapi akurasi pada kasus yang diterima berpotensi meningkat. Hubungan antara akurasi dan *coverage* perlu dianalisis dalam eksperimen.

#### e. Penyesuaian pseudocode

Pseudocode pada Bab IV perlu menunjukkan proses perhitungan skor akhir. Setelah kandidat lolos tahap *filtering*, alurnya dapat diringkas menjadi:

```text
hitung skor leksikal dan semantik
hitung kesesuaian domain, atribut, dan granularitas
lakukan reranking LLM beberapa kali
hitung skor konsistensi
normalisasi seluruh komponen
hitung skor akhir berbobot
pilih kandidat dengan skor tertinggi
jika skor dan konsistensi memenuhi threshold:
    terima kandidat
selainnya:
    abstain dan kirim untuk validasi ahli
```

Pseudocode tersebut membuat hubungan antara teori pada Bab III dan implementasi pada Bab IV dapat ditelusuri dengan jelas.

#### f. Penyesuaian rancangan ablation study

Rancangan ablasi perlu mengukur kontribusi kelompok komponen formula. Varian yang dapat diuji antara lain:

1. tanpa skor leksikal;
2. tanpa skor semantik;
3. tanpa skor domain;
4. tanpa skor atribut;
5. tanpa skor granularitas;
6. tanpa skor konsistensi atau *self-consistency*;
7. hanya retrieval tanpa reranking; dan
8. reranking LLM tanpa skor retrieval.

Ablasi dapat dilakukan satu komponen pada satu waktu agar perubahan performa dapat dikaitkan dengan komponen yang dihilangkan.

#### g. Uji sensitivitas

Selain ablasi, Bab IV perlu menjelaskan uji sensitivitas terhadap:

- nilai bobot setiap komponen;
- nilai Top-$k$ kandidat;
- threshold filtering;
- threshold penerimaan akhir;
- jumlah pengulangan LLM untuk *self-consistency*; dan
- perubahan model sparse, dense, atau reranker.

Uji sensitivitas diperlukan untuk mengetahui apakah sistem stabil atau sangat bergantung pada konfigurasi tertentu.

#### h. Penyesuaian dataset dan gold standard

Jika skor domain, atribut, dan granularitas akan dievaluasi secara langsung, anotasi *gold standard* perlu memuat informasi yang cukup, misalnya:

- jenis atau domain entitas;
- terminologi target;
- kode yang benar;
- atribut klinis yang harus dipertahankan;
- tingkat kekhususan yang diharapkan; dan
- keputusan apakah kasus boleh dipetakan otomatis atau memerlukan validasi ahli.

Tanpa anotasi tersebut, evaluasi hanya dapat menilai kode akhir dan tidak dapat menganalisis sumber kesalahan setiap komponen skor.

#### i. Penyesuaian evaluasi

Formula skor akhir adalah mekanisme pengambilan keputusan, bukan metrik evaluasi. Karena itu, keberhasilannya tetap dinilai menggunakan metrik pada Bab III, seperti Accuracy@1, Accuracy@$k$, MRR, *coverage*, konsistensi, dan efisiensi.

Evaluasi juga sebaiknya membedakan:

- *retrieval error*: kandidat benar tidak masuk Top-$k$;
- *filtering error*: kandidat benar ditemukan tetapi dibuang;
- *reranking error*: kandidat benar tersedia tetapi tidak mendapat skor tertinggi;
- *abstention error*: sistem menolak kasus yang sebenarnya dapat dipetakan; dan
- *overconfident error*: sistem menerima kandidat yang salah dengan skor tinggi.

### 3. Hubungan yang Diharapkan Antarbab

Setelah penyesuaian, alur argumentasi disertasi menjadi:

1. **Bab II** menunjukkan bahwa metode terdahulu belum secara bersamaan menyelesaikan masalah variasi bahasa Indonesia, multi-terminologi, teks panjang, dan pemilihan kandidat berbasis banyak aspek.
2. **Bab III** menyediakan landasan teori dan formula matematis untuk retrieval, filtering, reranking, konsistensi, serta skor akhir kandidat.
3. **Bab IV** menjelaskan sumber setiap skor, normalisasi, penentuan bobot, threshold, implementasi algoritma, rancangan ablasi, dan prosedur evaluasinya.

Dengan pembagian tersebut, formula tidak menjadi tambahan yang terisolasi. Formula berfungsi sebagai penghubung antara kesenjangan penelitian yang ditemukan pada Bab II, landasan matematis pada Bab III, dan metode implementasi serta pengujian pada Bab IV.

---

## G. Dasar Referensi dan Status Kebaruan Formula

Tidak seluruh formula dalam dokumen ini berasal secara langsung dari artikel yang sudah tersedia pada `term-mapping.bib`. Formula-formula tersebut perlu dibedakan menjadi formula yang diadaptasi dari literatur, formula matematika baku, formalisasi dari proses CDE-Mapper, dan formula baru yang diusulkan untuk penelitian.

Pembedaan ini penting agar formula rancangan penelitian tidak keliru ditulis sebagai formula milik Gilani dkk. atau peneliti terdahulu.

### 1. Formula yang memiliki dasar langsung dari referensi yang sudah tersedia

#### a. Formulasi probabilistik RAG

Formula:

$$
p(y\mid q)
=
\sum_{z\in Z_k(q)}
p_{\eta}(z\mid q)
p_{\theta}(y\mid q,z)
$$

memiliki dasar langsung dari kerangka RAG yang diperkenalkan oleh Lewis dkk. Referensinya sudah tersedia dalam `term-mapping.bib` dengan key:

```text
lewis_retrieval-augmented_2021
```

Notasi dalam dokumen ini telah disesuaikan dengan konteks pemetaan terminologi klinis. Karena itu, formula dapat diperkenalkan dengan kalimat:

> Mengadaptasi formulasi RAG dari Lewis dkk., probabilitas keluaran pada proses pemetaan dapat dinyatakan sebagai ....

#### b. Distribusi probabilitas kandidat retrieval

Penggunaan *softmax* untuk mengubah skor kandidat menjadi distribusi probabilitas juga konsisten dengan formulasi *neural retriever*. Formula ini dapat dikaitkan dengan referensi Lewis dkk., meskipun notasinya disederhanakan untuk kebutuhan penelitian.

### 2. Formula baku yang memerlukan sumber metodologis tambahan

Beberapa formula merupakan formula umum atau baku dalam bidang *information retrieval*, tetapi referensi sumber utamanya belum tersedia secara khusus pada `term-mapping.bib`.

#### a. Cosine similarity dan SapBERT

Formula *cosine similarity* adalah ukuran umum untuk membandingkan dua vektor embedding. Penggunaan SapBERT dalam CDE-Mapper memang didukung oleh artikel Gilani dkk., tetapi jika Bab III menjelaskan cara kerja atau mekanisme representasi SapBERT secara khusus, sebaiknya ditambahkan artikel asli SapBERT ke `term-mapping.bib`.

Referensi tambahan yang diperlukan adalah artikel yang memperkenalkan SapBERT untuk penyelarasan representasi entitas biomedis.

#### b. Sparse retrieval dan SPLADE

Formula:

$$
s_{\mathrm{sparse}}(q,c)
=
\mathbf{w}_q^{\top}\mathbf{w}_c
$$

merupakan representasi umum proses pemeringkatan pada ruang vektor sparse. Artikel CDE-Mapper mendukung penggunaan SPLADE sebagai komponen retrieval, tetapi bukan sumber utama formula SPLADE. Jika formula tersebut dimasukkan ke Bab III, artikel asli SPLADE sebaiknya ditambahkan ke `term-mapping.bib`.

#### c. Reciprocal Rank Fusion

Formula RRF:

$$
s_{\mathrm{RRF}}(c)
=
\sum_{m=1}^{M}\frac{1}{k_0+r_m(c)}
$$

berasal dari metode *Reciprocal Rank Fusion*. Referensi asli metode tersebut belum terdapat dalam `term-mapping.bib`. Jika RRF benar-benar digunakan dalam arsitektur atau eksperimen, perlu ditambahkan referensi Cormack, Clarke, dan Büttcher tentang RRF.

Jika RRF hanya ditampilkan sebagai alternatif yang tidak digunakan dalam penelitian, formula dapat dihilangkan untuk menjaga fokus naskah.

#### d. Self-consistency

CDE-Mapper menggunakan *self-consistency prompting*, sehingga prosesnya dapat didukung oleh key:

```text
gilani_cde-mapper_2025
```

Namun, formula rerata skor, varians, dan proporsi label mayoritas yang ditulis dalam dokumen ini bukan persamaan yang secara eksplisit diberikan oleh Gilani dkk. Formula tersebut merupakan formalisasi statistik dari proses pengulangan keputusan. Jika konsep *self-consistency* dibahas sebagai metode umum, sebaiknya ditambahkan artikel dasar tentang *self-consistency* pada LLM.

### 3. Formula yang merupakan formalisasi proses CDE-Mapper

Formula berikut dibangun berdasarkan tahapan yang dijelaskan dalam artikel CDE-Mapper, tetapi persamaan matematisnya merupakan formalisasi yang disusun untuk naskah penelitian ini:

1. dekomposisi kueri menjadi himpunan subkueri;
2. penggabungan kandidat dari seluruh subkueri;
3. skor ensemble SPLADE dan SapBERT;
4. agregasi skor dari beberapa subkueri;
5. penyaringan berdasarkan metadata dan threshold;
6. kategori relevansi pada *two-step reranking*; dan
7. confidence berbasis pengulangan penilaian LLM.

Formula-formula tersebut dapat menggunakan `gilani_cde-mapper_2025` sebagai dasar konseptual, tetapi harus diperkenalkan dengan ungkapan seperti:

> Berdasarkan alur CDE-Mapper, proses tersebut dapat diformalkan dalam penelitian ini sebagai ....

Formula tersebut tidak boleh diperkenalkan dengan kalimat:

> Gilani dkk. merumuskan formula tersebut sebagai ....

kecuali persamaannya memang ditemukan secara eksplisit dalam artikel asli.

### 4. Formula yang merupakan usulan baru penelitian

Formula berikut merupakan ide atau rancangan baru dalam dokumen ini dan tidak berasal langsung dari referensi terdahulu:

1. skor reranking multi-aspek yang menggabungkan semantik, domain, atribut, dan granularitas;
2. skor akhir yang menggabungkan retrieval dengan penilaian LLM;
3. kategori relevansi berdasarkan tiga threshold;
4. keputusan akhir dengan mekanisme *abstain*;
5. penalti inkonsistensi untuk pemetaan CDE komposit; dan
6. skor akhir terpadu enam komponen.

Formula skor akhir terpadu:

$$
S_{\mathrm{akhir}}(q,c)
=
w_lS_{\mathrm{leksikal}}
+w_sS_{\mathrm{semantik}}
+w_dS_{\mathrm{domain}}
+w_aS_{\mathrm{atribut}}
+w_gS_{\mathrm{granularitas}}
+w_kS_{\mathrm{konsistensi}}
$$

harus diperkenalkan sebagai formula yang diusulkan dalam penelitian. Kalimat yang disarankan adalah:

> Dalam penelitian ini, diusulkan fungsi skor akhir kandidat yang menggabungkan bukti leksikal, semantik, domain terminologi, kelengkapan atribut, granularitas konsep, dan konsistensi penilaian LLM.

Formula tersebut tidak memerlukan referensi sebagai formula terdahulu karena diposisikan sebagai usulan penelitian. Namun, setiap komponennya harus tetap didukung referensi yang relevan.

### 5. Ringkasan status formula

| Formula | Status | Referensi yang tersedia | Tindakan yang disarankan |
|---|---|---|---|
| Probabilitas RAG | Adaptasi langsung dari literatur | `lewis_retrieval-augmented_2021` | Cantumkan sitasi Lewis dkk. |
| Softmax kandidat retrieval | Formula umum neural retrieval | `lewis_retrieval-augmented_2021` | Jelaskan sebagai penyederhanaan formulasi retriever |
| Cosine similarity | Formula baku | Belum ada referensi metodologis khusus | Tambahkan artikel asli SapBERT jika mekanismenya dibahas |
| Sparse dot product | Formula baku retrieval | CDE-Mapper hanya mendukung penggunaan SPLADE | Tambahkan artikel asli SPLADE |
| Top-k dan argmax | Notasi matematika umum | Tidak membutuhkan sumber khusus | Definisikan seluruh simbol dengan jelas |
| Hybrid weighted score | Formalisasi/usulan | `gilani_cde-mapper_2025` sebagai dasar dual retrieval | Nyatakan sebagai formulasi penelitian ini |
| RRF | Metode dari literatur | Belum tersedia | Tambahkan artikel asli RRF jika digunakan |
| Dekomposisi dan union kandidat | Formalisasi alur CDE-Mapper | `gilani_cde-mapper_2025` | Gunakan frasa “dapat diformalkan sebagai” |
| Metadata dan threshold filtering | Formalisasi alur CDE-Mapper | `gilani_cde-mapper_2025` | Jangan dinyatakan sebagai persamaan asli Gilani |
| Confidence self-consistency | Formalisasi statistik | `gilani_cde-mapper_2025` mendukung prosesnya | Tambahkan artikel dasar self-consistency bila dibahas mendalam |
| Skor multi-aspek LLM | Usulan baru | Komponennya didukung beberapa literatur | Nyatakan sebagai kontribusi penelitian |
| Mekanisme abstain | Usulan metode | Belum ada referensi khusus | Tambahkan literatur selective prediction jika dijadikan metode utama |
| Skor CDE komposit | Usulan baru | CDE-Mapper mendukung dekomposisi CDE | Nyatakan sebagai kontribusi penelitian |
| Skor akhir enam komponen | Usulan utama penelitian | Tidak ada formula identik dalam referensi | Nyatakan secara eksplisit sebagai formula usulan |

### 6. Referensi tambahan yang sebaiknya dimasukkan

Jika seluruh formula dalam dokumen akan dimasukkan ke disertasi, `term-mapping.bib` sebaiknya dilengkapi dengan sumber asli untuk:

1. SPLADE;
2. SapBERT;
3. Reciprocal Rank Fusion;
4. *self-consistency* pada LLM; dan
5. *selective prediction* atau mekanisme abstain, apabila dijadikan bagian utama metode.

Referensi `gilani_cde-mapper_2025` tetap digunakan untuk mendukung arsitektur CDE-Mapper, yaitu *query decomposition*, dual retrieval, filtering, reranking, self-consistency, dan knowledge reservoir. Namun, referensi tersebut tidak boleh digunakan seolah-olah menjadi sumber seluruh persamaan yang diusulkan dalam dokumen ini.

### 7. Koreksi rekomendasi lokasi formula usulan

Karena formula skor akhir enam komponen bukan formula yang berasal dari Gilani dkk., penempatannya langsung di tengah Subbab 3.4.1 *Framework CDE-Mapper Gilani* dapat menimbulkan kesan bahwa formula tersebut merupakan bagian dari arsitektur asli CDE-Mapper.

Terdapat dua pilihan penempatan yang lebih aman:

1. menambahkan subbagian baru setelah pembahasan arsitektur dan temuan CDE-Mapper dengan judul seperti **“Formalisasi Adaptasi CDE-Mapper yang Diusulkan”**; atau
2. menempatkan formula lengkap pada Bab IV sebagai bagian metode usulan, sedangkan Bab III hanya menjelaskan komponen teoritis yang membentuk formula.

Jika formula tetap ditempatkan setelah pembahasan *two-step reranking*, harus ada kalimat transisi yang tegas:

> Berdasarkan komponen retrieval, filtering, dan reranking pada CDE-Mapper, penelitian ini mengusulkan suatu fungsi skor terpadu. Fungsi ini bukan bagian dari formula asli Gilani dkk., melainkan formalisasi yang dikembangkan untuk adaptasi pemetaan terminologi klinis Bahasa Indonesia.

Dengan penjelasan tersebut, pembaca dapat membedakan secara jelas antara arsitektur asli CDE-Mapper, formula baku dari literatur, dan kontribusi matematis yang diusulkan dalam penelitian.