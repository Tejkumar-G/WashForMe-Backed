from django.urls import path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView
from rest_framework.schemas import get_schema_view

from in_app.api.views.views import (
    ValidatePhoneSendOTP,
    ValidateOTP,
    GetUserDetails,
    GetWashCategories,
    GetWashItems,
    GetWashItemsBasedOnCategory,
    LogoutUser,
    WashCategoryItemRelationView,
    UserWashRelationView,
    CreateUserCategoryItemView,
    BookTimeSlot,
    CreateOrGetDeliverySlots,
    BookDeliveryTimeSlot,
    AddressHandler,
    ChangeCurrentAddress,
)
from in_app.api.views.pick_up_slot import CreateOrGetSchedulePickUpSlots, GetPickUpSlotOnDay

urlpatterns = [

    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs',
    ),
    path('validate_phone/', ValidatePhoneSendOTP.as_view()),
    path('validate_otp/', ValidateOTP.as_view()),
    path('logout/', LogoutUser.as_view()),
    # path('register/', Register.as_view()),
    # path('login/', LoginAPI.as_view()),

    path('get_all_addresses/', AddressHandler.as_view()),
    path('add_address/', AddressHandler.as_view()),
    path('update_address/<int:pk>/', AddressHandler.as_view()),
    path('change_current_address/<int:pk>/', ChangeCurrentAddress.as_view()),

    path('user_details/', GetUserDetails.as_view()),
    path('update_user/', GetUserDetails.as_view()),

    path('wash_categories/', GetWashCategories.as_view()),
    path('wash_items/', GetWashItems.as_view()),
    path('wash_items/<int:pk>/', GetWashItemsBasedOnCategory.as_view()),

    path('wash_category_item_relations/', WashCategoryItemRelationView.as_view()),
    path('user_wash_relations/', UserWashRelationView.as_view()),
    path('create_user_wash_relations/', CreateUserCategoryItemView.as_view()),

    path('get_pick_up_time_slots/', CreateOrGetSchedulePickUpSlots.as_view()),
    path('get_pick_up_slots/<str:pk>/', GetPickUpSlotOnDay.as_view()),
    path('book_pick_up_slot/', BookTimeSlot.as_view()),

    path('get_delivery_time_slots/<int:pk>/', CreateOrGetDeliverySlots.as_view()),
    path('book_delivery_slot/', BookDeliveryTimeSlot.as_view()),

]
