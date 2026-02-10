from rest_framework.pagination import CursorPagination

class CustomPostPagination(CursorPagination):
    page_size = 20
    cursor_query_param = "cursor"
    max_page_size = 30
    ordering = ["-created_at"]