from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import CandidateProfile, EmployerProfile
from .serializers import (
    CandidateProfileSerializer, CandidateProfilePublicSerializer,
    EmployerProfileSerializer,
)
from .permissions import IsCandidate, IsEmployer


# ─── Candidate ────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsCandidate])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def candidate_profile_me(request):
    try:
        profile = request.user.candidate_profile
    except CandidateProfile.DoesNotExist:
        profile = None

    if request.method == 'GET':
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CandidateProfileSerializer(profile).data)

    if request.method == 'POST':
        if profile is not None:
            return Response({'detail': 'Profile already exists. Use PUT/PATCH.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CandidateProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT / PATCH
    if profile is None:
        return Response({'detail': 'Profile not found. Use POST to create.'}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = CandidateProfileSerializer(profile, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_profile_detail(request, pk):
    """Public candidate profile — employers can view this."""
    profile = get_object_or_404(CandidateProfile, pk=pk)
    serializer = CandidateProfilePublicSerializer(profile)
    return Response(serializer.data)


# ─── Employer ─────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsEmployer])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def employer_profile_me(request):
    try:
        profile = request.user.employer_profile
    except EmployerProfile.DoesNotExist:
        profile = None

    if request.method == 'GET':
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployerProfileSerializer(profile).data)

    if request.method == 'POST':
        if profile is not None:
            return Response({'detail': 'Profile already exists. Use PUT/PATCH.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = EmployerProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if profile is None:
        return Response({'detail': 'Profile not found. Use POST to create.'}, status=status.HTTP_404_NOT_FOUND)
    partial = request.method == 'PATCH'
    serializer = EmployerProfileSerializer(profile, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def employer_profile_public(request, slug):
    """Public company profile page."""
    profile = get_object_or_404(EmployerProfile, company_slug=slug)
    return Response(EmployerProfileSerializer(profile).data)
