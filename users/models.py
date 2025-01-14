from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from PIL import Image
import re, os

from core.settings import MEDIA_ROOT


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name: str, max_length: int = None) -> str:
        self.delete(name)
        return name


def avatar_path(instance, _) -> str:
    if instance.id:
        return f'users/user_{instance.id}/avatar.webp'

    last = User.objects.last()
    if last:
        return f'users/user_{last.id + 1}/avatar.webp'
    return f'users/user_1/avatar.webp'


def validate_phone_number(phone: str):
    pattern = re.compile(
        r"^((8|\+374|\+994|\+995|\+375|\+7|\+380|\+38|\+996|\+998|\+993)[\- ]?)?\(?\d{3,5}\)?[\- ]?\d{1}[\- ]?\d{1}[\- ]?\d{1}[\- ]?\d{1}[\- ]?\d{1}(([\- ]?\d{1})?[\- ]?\d{1})?$")
    if not re.match(pattern, phone):
        raise ValidationError("Wrong phone number format")


class CustomUserManager(UserManager):
    def _create_user(self, email: str, password: str, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, password=password, **extra_fields)
        user.full_clean()
        user.set_password(user.password)
        user.save(using=self._db)

        return user

    def create(self, email: str = None, password: str = None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str = None, password: str = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone = models.CharField(unique=True, null=True, blank=True, validators=[validate_phone_number])
    name = models.CharField(max_length=254, default="Пользователь")
    avatar = models.ImageField(upload_to=avatar_path, default="userapp/default_avatar.webp", storage=OverwriteStorage)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        with Image.open(os.path.join(MEDIA_ROOT, self.avatar.name)) as im:
            im = im.resize((220, 220))
            im.save(os.path.join(MEDIA_ROOT, self.avatar.name))
