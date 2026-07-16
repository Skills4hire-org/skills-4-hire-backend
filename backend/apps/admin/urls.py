from django.urls import path, include

from .user_management.urls import user_managementpatterns
from .service_mangement.urls import service_patterns
from .support_disputes.urls import support_urlpatterns

urlpatterns = []
urlpatterns += user_managementpatterns
urlpatterns += service_patterns
urlpatterns += support_urlpatterns