"""Modul untuk memvalidasi dan menghitung offset karakter entitas serta BIO tagging."""

import re

def compute_entity_offsets(sentence: str, entities: list[dict]) -> list[dict]:
    valid_entities = []
    sent_lower = sentence.lower()

    for ent in entities:
        text = ent.get("text", "").strip()
        if not text:
            continue
        
        # Cari exact match dulu
        idx = sentence.find(text)
        if idx == -1:
            # Coba case-insensitive search
            idx = sent_lower.find(text.lower())
        
        if idx != -1:
            lbl = ent.get("label", "GEJALA").upper()
            if lbl == "TADA":
                lbl = "TANDA"
            valid_entities.append({
                "text": sentence[idx:idx + len(text)],
                "label": lbl,
                "assertion": ent.get("assertion", "PRESENT").upper(),
                "start": idx,
                "end": idx + len(text)
            })
        else:
            # Jika tidak ditemukan secara substring persis, coba cari kata-kata terpenting
            words = text.split()
            if words:
                sub_pattern = rf"\b{re.escape(words[0])}\b"
                m = re.search(sub_pattern, sentence, re.IGNORECASE)
                if m:
                    lbl = ent.get("label", "GEJALA").upper()
                    if lbl == "TADA":
                        lbl = "TANDA"
                    valid_entities.append({
                        "text": m.group(0),
                        "label": lbl,
                        "assertion": ent.get("assertion", "PRESENT").upper(),
                        "start": m.start(),
                        "end": m.end()
                    })
    
    # Sort by start offset
    valid_entities.sort(key=lambda x: x["start"])
    return valid_entities
