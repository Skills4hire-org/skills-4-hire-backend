from rest_framework.pagination import CursorPagination

class CustomPostPagination(CursorPagination):
    page_size = 50
    cursor_query_param = "cursor"
    max_page_size = 100
    ordering = ["-created_at"]