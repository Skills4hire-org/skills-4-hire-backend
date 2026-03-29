from rest_framework.pagination import PageNumberPagination


class EndorsementPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 20
    