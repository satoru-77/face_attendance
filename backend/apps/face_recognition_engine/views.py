import json
import numpy as np
from datetime import datetime

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import FaceEncoding, UserProfile
from .face_engine import face_engine
import logging

logger = logging.getLogger(__name__)


class EnrollmentStartView(APIView):
    """
    POST /api/face/enroll/start/
    Body: { "user_id": 5 }
    Response: { "message": "Ready to enroll", "user_id": 5, "total_photos_needed": 10 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required.'}, status=400)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        # Clear existing face encodings for re-enrollment
        FaceEncoding.objects.filter(user=user).delete()

        return Response({
            'message': f'Ready to enroll {user.get_full_name()}.',
            'user_id': user_id,
            'total_photos_needed': 10
        })


class EnrollmentPhotoView(APIView):
    """
    POST /api/face/enroll/photo/
    Form data: user_id (int), photo_number (int 1-10), image (file)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        photo_number = int(request.data.get('photo_number', 1))
        image_file = request.FILES.get('image')

        if not all([user_id, image_file]):
            return Response({'error': 'user_id and image are required.'}, status=400)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        image_bytes = image_file.read()
        result = face_engine.process_enrollment_photo(image_bytes)

        if result['error']:
            return Response({'error': result['error'], 'photo_number': photo_number}, status=400)

        # Save embedding to database
        FaceEncoding.objects.create(
            user=user,
            embedding=result['embedding'],
            photo_number=photo_number,
            quality_score=result['quality_score'],
            is_primary=False
        )

        return Response({
            'success': True,
            'photo_number': photo_number,
            'quality_score': result['quality_score'],
            'message': f'Photo {photo_number}/10 captured successfully.'
        })


class EnrollmentCompleteView(APIView):
    """
    POST /api/face/enroll/complete/
    Body: { "user_id": 5 }
    Averages all 10 embeddings, adds to FAISS index.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required.'}, status=400)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        encodings = FaceEncoding.objects.filter(user=user, is_primary=False)
        if encodings.count() < 5:
            return Response({'error': f'Need at least 5 photos. Only {encodings.count()} captured.'}, status=400)

        # Average all embeddings
        embeddings_list = [np.array(enc.embedding, dtype=np.float32) for enc in encodings]
        averaged = face_engine.average_embeddings(embeddings_list)

        # Save averaged embedding as primary
        FaceEncoding.objects.filter(user=user, is_primary=True).delete()
        FaceEncoding.objects.create(
            user=user,
            embedding=averaged.tolist(),
            photo_number=0,
            quality_score=float(np.mean([enc.quality_score for enc in encodings])),
            is_primary=True
        )

        # Add to FAISS index
        face_engine.add_to_index(user.id, averaged)

        # Update UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_face_enrolled = True
        profile.enrollment_date = datetime.now()
        profile.save()

        return Response({
            'success': True,
            'message': f'{user.get_full_name()} enrolled successfully.',
            'photos_used': encodings.count(),
            'user_id': user_id
        })


class EnrollmentStatusView(APIView):
    """GET /api/face/status/<user_id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            photos_count = FaceEncoding.objects.filter(user_id=user_id, is_primary=False).count()
            return Response({
                'user_id': user_id,
                'is_enrolled': profile.is_face_enrolled,
                'enrollment_date': profile.enrollment_date,
                'photos_captured': photos_count,
            })
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found.'}, status=404)
