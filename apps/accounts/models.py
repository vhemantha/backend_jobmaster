from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, role, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('role', 'candidate')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, extra.pop('role'), password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    CANDIDATE = 'candidate'
    EMPLOYER = 'employer'
    ROLE_CHOICES = [(CANDIDATE, 'Candidate'), (EMPLOYER, 'Employer')]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f'{self.email} ({self.role})'


class Notification(models.Model):
    APPLICATION_UPDATE = 'application_update'
    NEW_MATCH = 'new_match'
    SYSTEM = 'system'
    TYPE_CHOICES = [
        (APPLICATION_UPDATE, 'Application Update'),
        (NEW_MATCH, 'New Match'),
        (SYSTEM, 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=SYSTEM)
    title = models.CharField(max_length=200)
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.title} → {self.user.email}'
