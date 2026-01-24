from rest_framework.pagination import CursorPagination

class CustomBookingPagination(CursorPagination):
    page_size = 20
    cursor_query_param = "cursor"
    max_page_size = 50
    ordering = ["-created_at"]