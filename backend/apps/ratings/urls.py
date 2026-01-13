from django.urls import path, include

from .views import ReviewViewSet, RatingViewSet

review_list = ReviewViewSet.as_view({
    "get": "list",
    "post": "create"
})

review_detail = ReviewViewSet.as_view({
    "put": "update",
    "get": "retrieve",
    "delete": "destroy"
})


rating_list = RatingViewSet.as_view({
    "get": "list",
    "post": "create"
})

rating_detail = RatingViewSet.as_view({
    "put": "update",
    "get": "retrieve",
    "delete": "destroy"
})

urlpatterns = [
    path("profile/<uuid:profile_id>/reviews/", review_list, name="review-list"),
    path("profile/<uuid:profile_id>/ratings/", rating_list, name="rating-list"),
    path("profile/<uuid:profile_id>/ratings/<uuid:rating_pk>/", rating_detail, name="rating-detail"),
    path("profile/<uuid:profile_id>/reviews/<uuid:review_pk>/", review_detail, name="review-detail")
]