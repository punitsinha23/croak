from django.contrib import admin
from .models import Ribbit, Like, Comment

# Register your models here.
admin.site.register(Ribbit)
admin.site.register(Like)
admin.site.register(Comment)