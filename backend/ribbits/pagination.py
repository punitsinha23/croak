from rest_framework.pagination import CursorPagination

class FeedPagination(CursorPagination):
    ordering = '-created_at'  
