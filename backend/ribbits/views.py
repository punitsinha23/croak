from rest_framework import generics
from .serializers import PostSerializer, CommentSerializer
from .models import Ribbit, Like, Comment
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef
from django.db import models
from django.db.models import Q
from users.serializers import UserSerializer
from django.conf import settings


User = get_user_model()
class PostApiView(generics.CreateAPIView):
    queryset = Ribbit.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    

class RetrieveMyRibbitView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Ribbit.objects.filter(author=user)
            .annotate(
                likes_count=Count("likes", distinct=True),
                is_liked=Exists(
                    Like.objects.filter(ribbit=OuterRef("pk"), user=user)
                )
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class DeleteUpdateRibbitApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer
    queryset = Ribbit.objects.all()
    
    def delete(self, request, *args, **kwargs):
        ribbit = self.get_object()
        if ribbit.author != request.user:
            return Response({"error": "You cannot delete someone else's ribbit."}, status=status.HTTP_403_FORBIDDEN)
        ribbit.delete()
        return Response({"message": "Ribbit deleted."}, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        ribbit = self.get_object()
        if ribbit.author != request.user:
            return Response({"error": "You cannot Edit someone else's ribbit."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
        

class LikeApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        ribbit = get_object_or_404(Ribbit, pk=pk)
        like, created = Like.objects.get_or_create(ribbit=ribbit, user=request.user)

        if not created:  # already liked → unlike
            like.delete()

        # always serialize after like/unlike
        serializer = PostSerializer(ribbit, context={"request": request})

        return Response(
            {
                "status": "liked" if created else "unliked",
                "likes_count": ribbit.likes.count(),
                "is_liked": created, 
                "ribbit": serializer.data,  
            },
            status=status.HTTP_200_OK
        )


        
class ListRibbitApiView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        return (
            Ribbit.objects.all()
            .annotate(
                likes_count=Count("likes", distinct=True),
                is_liked=Exists(
                    Like.objects.filter(ribbit=OuterRef("pk"), user=user)
                ) if user.is_authenticated else models.Value(False, output_field=models.BooleanField())
            )
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    

class LikedRibbitsApiView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Ribbit.objects.filter(likes__user=user)   # only liked by current user
            .annotate(likes_count=Count("likes"))
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class SearchApiView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q','').strip()
        if not query:
            return Response({'results': []})
        
        ribbits = Ribbit.objects.filter(
            Q(text__icontains=query) | Q(author__username__icontains=query)
        )
        ribbit_serializer = PostSerializer(ribbits, many=True,context={"request": request})

        users = User.objects.filter(
            Q(username__icontains=query) | Q(bio__icontains=query)
        )
        user_serializer = UserSerializer(users, many=True,context={"request": request})

        return Response({
            "ribbits": ribbit_serializer.data,
            "users": user_serializer.data,
        })

class CommentApiView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ribbit_id = self.kwargs.get('pk')
        return Comment.objects.filter(ribbit_id=ribbit_id).order_by('-created_at')

    def perform_create(self, serializer):
        ribbit_id = self.kwargs.get('pk')
        serializer.save(author=self.request.user, ribbit_id=ribbit_id)



