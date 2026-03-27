from rest_framework.pagination import CursorPagination

class CustomBookingPagination(CursorPagination):
    page_size = 5
    ordering = '-created_at'

class CustomPaymentRequestPagination(CursorPagination):
    page_size = 5
    ordering = '-requested_at'