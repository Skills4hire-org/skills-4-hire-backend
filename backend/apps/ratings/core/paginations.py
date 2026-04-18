from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django.db.models import Avg

from collections import OrderedDict


class ReviewPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 30
    ordering = '-created_at'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('pagination', OrderedDict([
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('page_size', self.page_size),
                ("ordering_field", self.ordering),
                ("total_reviews", self.page.paginator.count)
            ])),
            ('results', data)
        ]))

class RatingPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 30
    ordering = '-created_at'

    def get_paginated_response(self, data):
        rating_avg = self.page.paginator.object_list.aggregate(avg_rating=Avg("rating"))

        return Response({
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "overall_avg_rating": rating_avg['avg_rating'] or 0,
            "overall_rating_count": self.page.paginator.count,
            "result": data
        })