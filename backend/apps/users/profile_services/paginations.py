from rest_framework.pagination import PageNumberPagination

class ProfilePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 30