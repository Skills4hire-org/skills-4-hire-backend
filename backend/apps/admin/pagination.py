from rest_framework.pagination import PageNumberPagination


class AdminPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 100 