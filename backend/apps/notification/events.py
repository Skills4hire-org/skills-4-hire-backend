from enum import Enum

class NotificationEvents(Enum):
    JOB = "Job Update"
    MESSAGE = "Message Alert"
    EARNING = "Earning Notification"
    SYSTEM = "System Alert" 
    BOOKING = "Booking Alert"
    PAYMENT = "Payment Alert"