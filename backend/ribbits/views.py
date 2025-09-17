from rest_framework import generics
from .serializers import PostSerializer
from .models import Ribbit
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

class PostApiView(generics.CreateAPIView):
    queryset = Ribbit.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        return super().perform_create(serializer)

class RetrieveMyRibbitView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ribbit.objects.filter(author=self.request.user).order_by('-created_at')

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
        

    
        
    
class ListRibbitApiView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        return Ribbit.objects.all().order_by('-created_at')



