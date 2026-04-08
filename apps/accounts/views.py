from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, Notification
from .serializers import RegisterSerializer, UserSerializer, NotificationSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    from django.contrib.auth import authenticate
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        'user': UserSerializer(user).data,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logged out successfully.'})
    except Exception:
        return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


# ─── Notifications ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    qs = Notification.objects.filter(user=request.user)[:50]
    return Response(NotificationSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'count': count})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def notification_mark_read(request, pk):
    n = Notification.objects.filter(pk=pk, user=request.user).first()
    if not n:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return Response(NotificationSerializer(n).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notifications_read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'detail': 'All notifications marked as read.'})
