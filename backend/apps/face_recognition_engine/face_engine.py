import numpy as np
import faiss
import json
import os
import threading
import logging
from pathlib import Path

import cv2
import insightface
from insightface.app import FaceAnalysis

from django.conf import settings

logger = logging.getLogger(__name__)


class FaceRecognitionEngine:
    """
    Singleton service that holds:
    - InsightFace model (loaded once at startup)
    - FAISS index (in-memory, persisted to disk)
    - Mapping: FAISS index position → Django user_id
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern — only one engine instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._model_lock = threading.Lock()
        self.face_app = None
        self.faiss_index = None
        self.index_to_user_id = {}   # {faiss_position: user_id}
        self._load_model()
        self._load_faiss_index()

    # ─── Model Loading ────────────────────────────────────────────────────

    def _load_model(self):
        """
        Load InsightFace buffalo_l model.
        Downloads automatically on first run (~800MB).
        Subsequent runs use cached model.
        """
        try:
            logger.info("Loading InsightFace model...")

            model_dir = str(settings.BASE_DIR / '.insightface')
            os.makedirs(model_dir, exist_ok=True)

            self.face_app = FaceAnalysis(
                name='buffalo_l',
                root=model_dir,
                providers=['CPUExecutionProvider']
                # For GPU: providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )

            # det_size: detection resolution. 640x640 is good for single faces.
            # Use (1280, 1280) for classroom group photos.
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))

            logger.info("✅ InsightFace model loaded successfully.")

        except Exception as e:
            logger.error(f"❌ Failed to load InsightFace model: {e}")
            raise

    # ─── FAISS Index ──────────────────────────────────────────────────────

    def _load_faiss_index(self):
        """Load FAISS index from disk, or create a new empty one."""
        index_path = str(settings.FAISS_INDEX_PATH)
        mapping_path = str(settings.FAISS_MAPPING_PATH)

        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        if os.path.exists(index_path) and os.path.exists(mapping_path):
            try:
                self.faiss_index = faiss.read_index(index_path)
                with open(mapping_path, 'r') as f:
                    # Keys must be int (JSON stores them as strings)
                    raw = json.load(f)
                    self.index_to_user_id = {int(k): v for k, v in raw.items()}
                logger.info(f"✅ FAISS index loaded: {self.faiss_index.ntotal} embeddings.")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}. Creating new one.")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create a fresh FAISS flat L2 index for 512-dimensional vectors."""
        EMBEDDING_DIM = 512
        self.faiss_index = faiss.IndexFlatIP(EMBEDDING_DIM)
        # IndexFlatIP = Inner Product (cosine similarity with normalized vectors)
        self.index_to_user_id = {}
        logger.info("Created new empty FAISS index.")

    def _save_faiss_index(self):
        """Persist FAISS index to disk."""
        try:
            index_path = str(settings.FAISS_INDEX_PATH)
            mapping_path = str(settings.FAISS_MAPPING_PATH)
            faiss.write_index(self.faiss_index, index_path)
            with open(mapping_path, 'w') as f:
                json.dump(self.index_to_user_id, f)
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    # ─── Face Detection ───────────────────────────────────────────────────

    def decode_image(self, image_bytes):
        """Convert bytes from HTTP upload to numpy array (BGR for OpenCV)."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def detect_faces(self, image_bytes_or_array):
        """
        Detect all faces in an image.
        
        Returns list of face objects. Each has:
        - face.bbox: [x1, y1, x2, y2]
        - face.embedding: 512-D numpy array
        - face.det_score: detection confidence (0-1)
        """
        if isinstance(image_bytes_or_array, bytes):
            img = self.decode_image(image_bytes_or_array)
        else:
            img = image_bytes_or_array

        if img is None:
            raise ValueError("Could not decode image.")

        with self._model_lock:
            faces = self.face_app.get(img)

        return faces

    def detect_single_face(self, image_bytes):
        """
        For enrollment: detect exactly one face.
        Returns (face, error_message).
        """
        faces = self.detect_faces(image_bytes)

        if len(faces) == 0:
            return None, "No face detected. Please ensure your face is clearly visible."
        if len(faces) > 1:
            return None, f"Multiple faces detected ({len(faces)}). Please ensure only one person is in frame."

        face = faces[0]
        if face.det_score < 0.5:
            return None, f"Face quality too low ({face.det_score:.2f}). Please improve lighting."

        return face, None

    # ─── Embedding Generation ─────────────────────────────────────────────

    def get_embedding(self, face):
        """
        Extract normalized 512-D embedding from a detected face.
        Normalization ensures cosine similarity works correctly.
        """
        embedding = face.embedding
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.astype(np.float32)

    def average_embeddings(self, embeddings_list):
        """
        Average multiple embeddings (from 10 enrollment photos).
        Re-normalize after averaging.
        """
        avg = np.mean(embeddings_list, axis=0)
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm
        return avg.astype(np.float32)

    # ─── FAISS Operations ─────────────────────────────────────────────────

    def add_to_index(self, user_id, embedding):
        """
        Add a user's embedding to the FAISS index.
        Call this after enrollment is complete.
        """
        with self._model_lock:
            # Remove existing entries for this user (re-enrollment)
            self._remove_user_from_index(user_id)

            # Add new embedding
            position = self.faiss_index.ntotal
            embedding_2d = embedding.reshape(1, -1)
            self.faiss_index.add(embedding_2d)
            self.index_to_user_id[position] = user_id

            self._save_faiss_index()

        logger.info(f"Added user {user_id} to FAISS index at position {position}.")

    def _remove_user_from_index(self, user_id):
        """
        Remove an existing user from the index (for re-enrollment).
        FAISS flat index doesn't support deletion, so we rebuild.
        """
        if user_id not in self.index_to_user_id.values():
            return  # Not in index, nothing to do

        logger.info(f"Removing user {user_id} from FAISS index for re-enrollment...")
        # Collect all embeddings except the one being replaced
        old_total = self.faiss_index.ntotal
        if old_total == 0:
            return

        all_embeddings = faiss.rev_swig_ptr(self.faiss_index.get_xb(), old_total * 512)
        all_embeddings = all_embeddings.reshape(old_total, 512).copy()

        new_embeddings = []
        new_mapping = {}

        for pos, uid in self.index_to_user_id.items():
            if uid != user_id:
                new_pos = len(new_embeddings)
                new_embeddings.append(all_embeddings[pos])
                new_mapping[new_pos] = uid

        self._create_new_index()
        if new_embeddings:
            batch = np.array(new_embeddings, dtype=np.float32)
            self.faiss_index.add(batch)
        self.index_to_user_id = new_mapping

    def search(self, query_embedding, top_k=1):
        """
        Search the FAISS index for the closest matching face.
        
        Returns list of (user_id, similarity_score) tuples.
        similarity_score is 0-1 (cosine similarity).
        """
        if self.faiss_index.ntotal == 0:
            return []

        query = query_embedding.reshape(1, -1)
        distances, indices = self.faiss_index.search(query, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:   # FAISS returns -1 if not enough results
                continue
            user_id = self.index_to_user_id.get(idx)
            if user_id is not None:
                # Inner product with normalized vectors = cosine similarity (-1 to 1)
                # Convert to 0-100% confidence
                confidence = max(0, float(dist)) * 100
                results.append((user_id, confidence))

        return results

    # ─── High-Level API Methods ────────────────────────────────────────────

    def process_enrollment_photo(self, image_bytes):
        """
        Process a single enrollment photo.
        Returns: {'embedding': [...], 'quality_score': float, 'error': str or None}
        """
        face, error = self.detect_single_face(image_bytes)
        if error:
            return {'embedding': None, 'quality_score': 0, 'error': error}

        embedding = self.get_embedding(face)
        return {
            'embedding': embedding.tolist(),
            'quality_score': float(face.det_score),
            'error': None
        }

    def recognize_face(self, image_bytes, confidence_threshold=60.0):
        """
        For kiosk mode: Identify a single person from an image.
        
        Returns:
        {
            'user_id': int or None,
            'confidence': float (0-100),
            'error': str or None
        }
        """
        face, error = self.detect_single_face(image_bytes)
        if error:
            return {'user_id': None, 'confidence': 0, 'error': error}

        embedding = self.get_embedding(face)
        results = self.search(embedding, top_k=1)

        if not results:
            return {'user_id': None, 'confidence': 0, 'error': 'No enrolled faces in database.'}

        user_id, confidence = results[0]

        if confidence < confidence_threshold:
            return {
                'user_id': None,
                'confidence': confidence,
                'error': f'Face not recognized. Confidence {confidence:.1f}% is below threshold {confidence_threshold}%.'
            }

        return {'user_id': user_id, 'confidence': confidence, 'error': None}

    def recognize_classroom(self, image_bytes, confidence_threshold=60.0):
        """
        For classroom mode: Identify ALL faces in a group photo.

        Returns:
        {
            'recognized': [{'user_id': int, 'confidence': float, 'bbox': [x1,y1,x2,y2]}, ...],
            'unknown': [{'bbox': [x1,y1,x2,y2], 'confidence': float}, ...],
            'total_detected': int,
            'error': None
        }
        """
        # Use larger detection size for group photos
        with self._model_lock:
            self.face_app.prepare(ctx_id=0, det_size=(1280, 1280))
            faces = self.detect_faces(image_bytes)
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))  # Reset

        recognized = []
        unknown = []

        for face in faces:
            embedding = self.get_embedding(face)
            results = self.search(embedding, top_k=1)
            bbox = face.bbox.tolist()

            if results:
                user_id, confidence = results[0]
                if confidence >= confidence_threshold:
                    recognized.append({
                        'user_id': user_id,
                        'confidence': confidence,
                        'bbox': bbox
                    })
                else:
                    unknown.append({'bbox': bbox, 'confidence': confidence})
            else:
                unknown.append({'bbox': bbox, 'confidence': 0})

        return {
            'recognized': recognized,
            'unknown': unknown,
            'total_detected': len(faces),
            'error': None
        }


# Global singleton instance
face_engine = FaceRecognitionEngine()
