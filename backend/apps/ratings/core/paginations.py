from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django.db.models import Avg

from collections import OrderedDict

class ReviewPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 30
    ordering = '-created_at'

    def get_paginated_response(self, data):
        rating_avg = self.page.paginator.object_list.aggregate(avg_rating=Avg("ratings"))

        return Response({
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "overall_avg_rating": rating_avg['avg_rating'] or 0,
            "total_reviews": self.page.paginator.count,
            "result": data
        })