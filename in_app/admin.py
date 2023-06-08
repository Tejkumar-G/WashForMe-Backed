from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from in_app.forms import CustomUserCreationForm
from in_app.models import (
    User,
    PhoneOTP,
    WashItem,
    WashCategory,
    WashCategoryItemRelation,
    UserWashRelation,
    PickUpSchedule,
    PickUpSlotBook,
    Address,
    AddressType,
    UserAddress
)


# Register your models here.

class CustomUserAdmin(BaseUserAdmin):

    add_form = CustomUserCreationForm
    model = User
    list_display = ('email','phone', 'is_staff', 'is_active',)
    list_filter = ('email','phone','is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', )}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'is_staff', 'is_active', 'password', 'is_superuser')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.register(User, CustomUserAdmin)
admin.site.register(PhoneOTP)
admin.site.register(WashItem)
admin.site.register(WashCategory)
admin.site.register(WashCategoryItemRelation)
admin.site.register(UserWashRelation)
admin.site.register(PickUpSchedule)
admin.site.register(PickUpSlotBook)
admin.site.register(Address)
admin.site.register(AddressType)
admin.site.register(UserAddress)
