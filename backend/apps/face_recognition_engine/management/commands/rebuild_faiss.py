from django.core.management.base import BaseCommand
from apps.accounts.models import FaceEncoding
from apps.face_recognition_engine.face_engine import face_engine
import numpy as np

class Command(BaseCommand):
    help = 'Rebuilds the FAISS index from the primary face encodings in the database.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Rebuilding FAISS index...'))
        
        # Clear existing index
        face_engine.faiss_index.reset()
        face_engine.index_to_user_id = {}
        
        # Get all primary encodings
        primary_encodings = FaceEncoding.objects.filter(is_primary=True)
        count = primary_encodings.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No primary encodings found in the database. Index is empty.'))
            face_engine._save_index()
            return

        success_count = 0
        for enc in primary_encodings:
            try:
                emb = np.array(enc.embedding, dtype=np.float32)
                face_engine.add_to_index(enc.user_id, emb)
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to add user {enc.user_id} to index: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully rebuilt FAISS index with {success_count} users.'))
