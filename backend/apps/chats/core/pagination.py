from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class MessagePagination(CursorPagination):
    """
    Cursor-based pagination optimized for messages.

    Cursor-based pagination is ideal for large message histories as it:
    - Doesn't require counting total results
    - Handles concurrent insertions well
    - Provides stable ordering
    """

    page_size = 20
    page_size_query_param = 'page_size'
    page_size_query_description = 'Number of messages to return'
    max_page_size = 100
    ordering = '-created_at'  # Most recent first
    cursor_query_param = 'cursor'
    cursor_query_description = 'The pagination cursor value'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('pagination', OrderedDict([
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('page_size', self.page_size),
            ])),
            ('results', data)
        ]))


class ConversationPagination(PageNumberPagination):
    """
    Pagination for conversation lists.

    Uses page-based pagination for conversations since users typically
    don't have thousands of conversations.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_size_query_description = 'Number of conversations per page'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('pagination', OrderedDict([
                ('count', self.page.paginator.count),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('page_size', self.page_size),
                ('total_pages', self.page.paginator.num_pages),
                ('current_page', self.page.number),
            ])),
            ('results', data)
        ]))