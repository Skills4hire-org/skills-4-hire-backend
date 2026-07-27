
from .user_management.urls import user_managementpatterns
from .service_mangement.urls import service_urlpatterns
from .support_disputes.urls import support_urlpatterns
from .booking.urls import urlpatterns as booking_urlpatterns
from .auth.urls import urlpatterns as auth_urlpatterns

urlpatterns = []
urlpatterns += user_managementpatterns
urlpatterns += service_urlpatterns
urlpatterns += support_urlpatterns
urlpatterns += booking_urlpatterns
urlpatterns += auth_urlpatterns