

class DuplicateBookingError(Exception):
    """ Prevent creating booking with the same idempotency"""