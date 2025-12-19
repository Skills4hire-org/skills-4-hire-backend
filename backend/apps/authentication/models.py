from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
import uuid
from autoslug import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField
from apps.authentication import otp_models

class CustomBaseUserManager(BaseUserManager):
    """ 
         Fullname:backend.apps.models.CustomBaseUserManager

         A Custom manager for handling user registrations for both admins and non admins users

        - Register user 
            - user = User.objects.create_user(email="example@g.com, password='user')

        - Register Admin user
            - admin_user = User.objects.creat_superuser(email="admin@g.com", password="admin")
                admin_user.is_superuser = True
                admin_user.is_staff = True
        
        Methods 
            - def create_user(email, password, **extra_fields)
            - def create_superuser(email, password, **extra_fields)
    """

    def create_user(self, email, password, **extra_fields):
        """
            A method for handling User registrations with simple base  validations and password hashing and salting
        """
        if email is None:
            raise ValueError("email is required for account registration")
        
        valid_email = self.normalize_email(email)
        if not valid_email:
            raise ValueError("Email provided is invalid, check nd try again")
        
        user = self.model(email=valid_email, **extra_fields)

        # hash user password using the set_password method
        user.set_password(password) # both hash and salt user password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """ Create and save a super user instane """
        if not extra_fields.get("is_superuser"):
            raise ValueError("super user field must be created ")
        if not extra_fields.get("is_staff"):
            raise ValueError("is_staff must be provided")
        
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)

        return self.create_user(email=email, pasword=password, **extra_fields)


    def create_superuser(self, email, password, **extra_fields):
        """  
            A method for handling admin user account registrations 
        """

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that supports using email instead of username.

    Attributes:
        email (EmailField): The primary unique identifier for the user account.
        first_name (CharField): The user's given name (max 30 chars).
        is_active (BooleanField): Designates whether this user should be treated as active.
        date_joined (DateTimeField): The date and time the account was created.
        other fields 
    """

    class RoleChoices(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLIENT = "CLIENT", "Client"
        SERVICE_PROVIDER = "SERVICE_PROVIDER", "Service_provider"


    user_id =  models.UUIDField(max_length=20, 
                                unique=True, 
                                default=uuid.uuid4, 
                                primary_key=True
                                )
    slug = AutoSlugField(populate_from="first_name",
                        default=None, 
                        null=True, 
                        unique=True, 
                        )
                

    email = models.EmailField(
        unique=True, 
        blank=False, 
        max_length=100
    )
    phone = PhoneNumberField(max_length=50, unique=True, blank=False)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    # user roles in [admin, client, service_provide]
    role = models.CharField(max_length=30, choices=RoleChoices.choices, default=RoleChoices.SERVICE_PROVIDER)

    # Boolean fields
    is_active = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)

    # soft delete user account
    is_deleted = models.BooleanField(default=False, editable=True)

    # Monitor instances
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone", "role"]
    objects = CustomBaseUserManager()


    @property
    def is_service_provider(self):
        """ Check and return True is the user instance.role == service_provider"""
        return self.role == RoleChoices.SERVICE_PROVIDER

    @property
    def is_client(self):
        """ Check and return True if the user instance.role == client"""
        return self.role == RoleChoices.CLIENT

    @property
    def is_admin(self):
        " Check and return True is the user instance.role == Admin"
        return (
            self.role == RoleChoices.ADMIN,
            self.is_superuser,
            self.is_staff
        )

    @property
    def full_name(self):
        """ Concat each instance (first_name and last_name) and return result """
        name = f"{self.first_name} {self.last_name}"
        return name

    def __str__(self):
        " string rep. of user instances"
        return f"CustomUser({self.email}, {self.phone}, {self.full_name}, {self.role})"


    class Meta:
        ordering = ["-created_at"]
        db_table = "users"
        indexes = [
            models.Index(fields=["email"], name="email_idx"),
            models.Index(fields=["phone"], name="phone_idx"),
            models.Index(fields=["role"], name="role_idx"),
            models.Index(fields=["first_name", "last_name"], name="first_last_name_idx"),

        ]

        verbose_name_plural = "users"

    