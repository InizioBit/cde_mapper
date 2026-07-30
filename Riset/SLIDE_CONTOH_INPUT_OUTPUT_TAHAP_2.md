# Slide Tambahan - Contoh Input dan Output Tahap 2

## Tahap 2: Ekstraksi Entitas Klinis dari Teks Panjang

**Input setelah Tahap 1:**

```text
Dokter, anak saya umur 2 tahun panas 38.5 °C
dari kemarin, sudah dikasih paracetamol 3x1
tapi belum turun. Terima kasih.
```

**Output Tahap 2:**

```json
{
  "document_id": "alodokter_000001_question",
  "entities": [
    {
      "mention": "umur 2 tahun",
      "base_entity": "umur",
      "entity_type": "demographic",
      "domain": "observation",
      "value": "2",
      "unit": "tahun",
      "assertion": "present",
      "temporal": "present",
      "experiencer": "patient"
    },
    {
      "mention": "panas 38.5 °C",
      "base_entity": "demam",
      "entity_type": "symptom",
      "domain": "condition",
      "value": "38.5",
      "unit": "°C",
      "associated_entities": ["dari kemarin"],
      "assertion": "present",
      "temporal": "present",
      "experiencer": "patient"
    },
    {
      "mention": "paracetamol 3x1",
      "base_entity": "paracetamol",
      "entity_type": "drug",
      "domain": "drug",
      "frequency": "3x1",
      "assertion": "present",
      "temporal": "past",
      "experiencer": "patient"
    },
    {
      "mention": "belum turun",
      "base_entity": "demam belum membaik",
      "entity_type": "clinical_finding",
      "domain": "observation",
      "associated_entities": ["panas 38.5 °C", "paracetamol 3x1"],
      "assertion": "present",
      "temporal": "present",
      "experiencer": "patient"
    }
  ]
}
```

**Pesan utama:** Tahap 2 mengubah satu narasi panjang menjadi banyak entitas klinis terstruktur lengkap dengan tipe, nilai, unit, negasi, temporalitas, dan experiencer.

> **Note presenter:** Tekankan bahwa ini belum tahap mapping kode. Output Tahap 2 menjadi input untuk routing terminologi, query decomposition, retrieval, filtering, dan reranking.
