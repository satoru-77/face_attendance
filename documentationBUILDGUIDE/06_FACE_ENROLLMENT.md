# 06 — Face Enrollment (InsightFace + FAISS)

## Model: InsightFace buffalo_l

The `buffalo_l` model pack includes 5 ONNX models loaded at server startup:

| Model File | Role | Input Size |
|-----------|------|-----------|
| `det_10g.onnx` | Face detection (finds bounding boxes) | 640×640 |
| `w600k_r50.onnx` | Face recognition (512-D embeddings) | 112×112 |
| `1k3d68.onnx` | 3D landmark detection (68 points) | 192×192 |
| `2d106det.onnx` | 2D landmark detection (106 points) | 192×192 |
| `genderage.onnx` | Gender and age estimation | 96×96 |

For attendance, only **detection** and **recognition** are critical.

---

## FaceRecognitionEngine (Singleton)

```python
# face_engine.py — singleton pattern
face_engine = FaceRecognitionEngine()  # Created once at module import
```

The singleton holds:
1. The loaded InsightFace `FaceAnalysis` object
2. The FAISS index (in memory)
3. The index→user_id mapping dict

A threading lock (`_model_lock`) protects concurrent access to the model.

---

## Embedding Pipeline

```
Raw Image (JPEG bytes)
    │
    ▼ decode_image()
OpenCV numpy array (BGR)
    │
    ▼ face_app.get(img)   [InsightFace]
List of Face objects
    │  face.bbox         → bounding box [x1, y1, x2, y2]
    │  face.embedding    → 512-D numpy array (unnormalized)
    │  face.det_score    → detection confidence (0–1)
    │
    ▼ get_embedding()
Normalized 512-D embedding (unit vector)
    │
    ▼ add_to_index() or search()
FAISS
```

### Why normalize?
FAISS `IndexFlatIP` computes **inner product**. For unit vectors, inner product == cosine similarity.
Cosine similarity ranges from -1 (opposite) to 1 (identical).
We clamp negative values to 0 and multiply by 100: `confidence = max(0, dist) * 100` → **0–100%**.

---

## Enrollment Embedding Strategy

Instead of using a single photo embedding, we average 10 photos:

```python
def average_embeddings(self, embeddings_list):
    avg = np.mean(embeddings_list, axis=0)  # Element-wise mean
    norm = np.linalg.norm(avg)
    avg = avg / norm                         # Re-normalize
    return avg.astype(np.float32)
```

**Why 10 photos?** Different poses, lighting, expressions.
The averaged embedding is more robust and generalizes better at recognition time.

---

## FAISS Index Management

### Index type: `IndexFlatIP`
- Exact (no approximate) nearest-neighbor search
- Inner Product (cosine similarity with normalized vectors)
- 512 dimensions (matches InsightFace embedding size)
- Can handle 100,000+ embeddings at millisecond speed on CPU

### Persistence
```
media/faiss_index.bin     ← Binary FAISS index
media/faiss_mapping.json  ← {position: user_id}
```

Both files are **written to disk on every enrollment** and **read on server startup**.

### Adding a user
```python
face_engine.add_to_index(user_id=5, embedding=averaged)
# Internally:
# 1. Remove old entry for user 5 if exists (re-enrollment)
# 2. faiss_index.add(embedding_2d)
# 3. index_to_user_id[new_position] = 5
# 4. Save both files to disk
```

### Searching (at check-in)
```python
results = face_engine.search(query_embedding, top_k=1)
# Returns: [(user_id, confidence_0_to_100)]
# e.g.:    [(5, 87.3)]
```

---

## Confidence Thresholds

| Threshold | Where Applied | Value |
|-----------|--------------|-------|
| Kiosk check-in | `KioskCheckinView` | **70%** minimum |
| Enrollment photo quality | `detect_single_face()` | 0.5 det_score |
| Classroom mode | `recognize_classroom()` | 60% default |

> A confidence of 70+ means the system is 70% similar to the stored embedding. In practice, the same person consistently scores 85–99%.

---

## Detection Modes

### Single face (kiosk / enrollment)
```python
face_app.prepare(ctx_id=0, det_size=(640, 640))
faces = face_app.get(img)
# Expects exactly 1 face
```

### Group photo (classroom)
```python
face_app.prepare(ctx_id=0, det_size=(1280, 1280))
faces = face_app.get(img)
# Detects all faces, matches each one
face_app.prepare(ctx_id=0, det_size=(640, 640))  # Reset
```

---

## What's Stored in DB vs FAISS

| Data | Where stored |
|------|-------------|
| Individual photo embeddings (1–10) | PostgreSQL `FaceEncoding` (`is_primary=False`) |
| Averaged primary embedding | PostgreSQL `FaceEncoding` (`is_primary=True`) |
| FAISS index (for fast search) | Disk: `media/faiss_index.bin` |
| FAISS mapping | Disk: `media/faiss_mapping.json` |

The PostgreSQL embeddings serve as backup and for audit. The FAISS files are the operational index.

> ⚠️ If you delete the FAISS files, you must re-enroll all students OR write a management command to rebuild the index from the DB primary embeddings.
