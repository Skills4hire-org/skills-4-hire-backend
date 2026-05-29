from rest_framework.pagination import PageNumberPagination

class CustomBookingPagination(PageNumberPagination):
    page_size = 10
    ordering = '-created_at'

class CustomPaymentRequestPagination(PageNumberPagination):
    page_size = 5
    ordering = '-requested_at'