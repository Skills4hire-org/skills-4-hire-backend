from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from collections import OrderedDict

class AddressPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'


    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('pagination', OrderedDict([
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('page_size', self.page_size),
                ("ordering_field", self.ordering)
            ])),
            ('results', data)
        ]))