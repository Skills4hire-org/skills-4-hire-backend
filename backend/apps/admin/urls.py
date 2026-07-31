from .user_management.urls import user_managementpatterns
from .service_mangement.urls import service_urlpatterns
from .support_disputes.urls import support_urlpatterns
from .booking.urls import urlpatterns as booking_urlpatterns
from .auth.urls import urlpatterns as auth_urlpatterns
from .open_applications.urls import urlpatterns as application_urlpatterns

urlpatterns = [
    *user_managementpatterns, *service_urlpatterns, 
    *support_urlpatterns, *booking_urlpatterns, 
    *auth_urlpatterns, *application_urlpatterns
    ]