# Create your models here.
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    phone_regex = RegexValidator(regex=r'^((\+91?)|\+)?[6-9][0-9]{9}$',
                                 message="Phone number must be entered in the format +919999999999. Up to 10 digits "
                                         "allowed.")
    phone = models.CharField('Phone', validators=[phone_regex], max_length=17, unique=True, null=True)
    first_name = models.CharField(max_length=55, blank=None)
    last_name = models.CharField(max_length=55, blank=None)
    username = None
    USERNAME_FIELD = 'phone'
    dictionary = dict(availability='Yes', notifications='On', language='English', dark_mode='No')
    other_details = models.TextField(default=dictionary, blank=True)
    objects = UserManager()


class PhoneOTP(models.Model):
    phone_regex = RegexValidator(regex=r'^((\+91?)|\+)?[6-9][0-9]{9}$',
                                 message="Phone number must be entered in the format +919999999999. Up to 10 digits "
                                         "allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    otp = models.CharField(max_length=9, blank=True, null=True)
    count = models.IntegerField(default=0, help_text='Number of otp_sent')
    validated = models.BooleanField(default=False,
                                    help_text='If it is true, that means user '
                                              'have validate otp correctly in second API')
    otp_session_id = models.CharField(max_length=120, null=True, default="")
    email = models.CharField(max_length=50, null=True, blank=True, default=None, unique=True)

    def __str__(self):
        return str(self.phone) + ' is sent ' + str(self.otp)


class WashItem(models.Model):
    name = models.CharField(max_length=55, unique=True)
    image = models.FileField(upload_to='media/', null=True, blank=True)
    price = models.IntegerField()
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class ItemWithCount(models.Model):
    item = models.ForeignKey(WashItem, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.id


class WashCategory(models.Model):
    name = models.CharField(max_length=55, unique=True)
    image = models.FileField(upload_to='media/', null=True, blank=True)
    extra_per_item = models.IntegerField(default=0)
    items = models.ManyToManyField(WashItem, blank=True)

    def __str__(self):
        return self.name


class WashCategoryItemRelation(models.Model):
    category = models.ForeignKey(WashCategory, on_delete=models.CASCADE)
    items = models.ManyToManyField(WashItem)

    def __str__(self):
        return f'{self.category.name} category with id {self.id}'


class UserWashRelation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wash_category_relations = models.ManyToManyField(WashCategoryItemRelation)

    def __str__(self):
        return f'{self.id}'


class PickUpSchedule(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    available_quota = models.PositiveIntegerField()
    filled_quota = models.PositiveIntegerField(default=0)
    date = models.DateField()
    schedule_completed = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} with id {self.id}"

    def is_available(self) -> bool:
        return self.available

    def make_unavailable(self):
        self.available = False

    def make_schedule_completed(self):
        self.schedule_completed = True


class PickUpSlotBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pick_up_slot = models.ForeignKey(PickUpSchedule, on_delete=models.CASCADE)
    user_wash_relation = models.ForeignKey(UserWashRelation, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.phone} at {self.pick_up_slot.start_time}-{self.pick_up_slot.end_time} id {self.id}'


class DeliverySchedule(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    available_quota = models.PositiveIntegerField()
    filled_quota = models.PositiveIntegerField(default=0)
    date = models.DateField()
    schedule_completed = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    def is_available(self) -> bool:
        return self.available

    def make_unavailable(self):
        self.available = False

    def make_schedule_completed(self):
        self.schedule_completed = True

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} with id {self.id}"


class BookDeliverySlot(models.Model):
    pick_up_slot = models.ForeignKey(PickUpSlotBook, on_delete=models.CASCADE)
    delivery_slot = models.ForeignKey(DeliverySchedule, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.pick_up_slot.user.phone} at {self.delivery_slot.start_time}-' \
               f'{self.delivery_slot.end_time} id {self.id}'


class Address(models.Model):
    address_line_one = models.CharField(max_length=55)
    address_line_two = models.CharField(max_length=55)
    city = models.CharField(max_length=55)
    postcode = models.IntegerField()
    country = models.CharField(max_length=55)

    def __str__(self):
        return f'{self.id}'


class AddressType(models.Model):
    type = models.CharField(max_length=55)

    def __str__(self):
        return self.type


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    address_type = models.ForeignKey(AddressType, on_delete=models.CASCADE)
    current_address = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.id} - {self.address.id} - {self.address_type.type}'


class Repayment(models.Model):
    name = models.CharField(max_length=55)
    mode = models.CharField(max_length=55)
    status = models.CharField(max_length=55)
    amount = models.IntegerField()


class Payment(models.Model):
    total_amount = models.IntegerField()
    repayment = models.ManyToManyField(Repayment, default=None)


class Order(models.Model):
    address = models.ForeignKey(UserAddress, on_delete=models.DO_NOTHING)
    pickup = models.ForeignKey(PickUpSlotBook, on_delete=models.DO_NOTHING)
    delivery = models.ForeignKey(BookDeliverySlot, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=55)
    picked_up_time = models.TimeField(default=None)
    delivered_time = models.DateField(default=None)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    picked_up_person = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='picked_up_person')
    delivered_person = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='delivered_person')

