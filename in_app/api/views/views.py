import ast
import datetime
import http.client
import random

from django.contrib.auth import login
from django.forms import model_to_dict
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView
from rest_framework import status, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from in_app.api.signals import update_item_count_on_relation_save

from in_app.api.serializer import (
    CreateUserSerializer,
    LoginSerializer,
    UserSerializer,
    WashCategorySerializer,
    WashItemSerializer,
    WashCategoryItemRelationSerializer,
    UserWashRelationSerializer,
    PickUpScheduleSerializer,
    SlotBookDetailSerializer,
    DeliveryScheduleSerializer,
    DeliverySlotBookDetailSerializer,
    UserAddressSerializer,
    UserAddressSerializerViewOnly,
    AddressSerializer,
    AddressTypeSerializer,
)
from in_app.models import (
    User,
    PhoneOTP,
    WashCategory,
    WashItem,
    WashCategoryItemRelation,
    UserWashRelation,
    PickUpSchedule,
    PickUpSlotBook,
    DeliverySchedule,
    BookDeliverySlot,
    UserAddress,
)

conn = http.client.HTTPConnection('2factor.in')


class ValidatePhoneSendOTP(APIView):

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone')
        email = request.data.get('email', None)

        if phone_number:
            phone = str(phone_number)
            user = User.objects.filter(phone__iexact=phone)
            if user.exists():
                key = self.send_otp(phone)
                if key:
                    if PhoneOTP.objects.filter(phone__iexact=phone).exists():
                        obj = PhoneOTP.objects.get(phone=phone)
                    else:
                        obj = PhoneOTP.objects.create(
                            phone=phone,
                            otp=key
                        )
                    return self.send_otp_via_sms(obj, phone, key)

            else:
                key = self.send_otp(phone)
                if key:
                    old = PhoneOTP.objects.filter(phone__iexact=phone)
                    if old.exists():
                        old = old.first()
                        count = old.count
                        if count > 10:
                            return Response({
                                'status': False,
                                'detail': 'Sending otp error. Limit Exceeded. Please Contact Customer support'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        old.count = count + 1
                        old.otp = key
                        old.save()
                        print('Count Increased', count)

                        return self.send_otp_via_sms(old, phone, key)
                    else:
                        obj = PhoneOTP.objects.create(
                            phone=phone,
                            otp=key,
                            email=email
                        )
                    return self.send_otp_via_sms(obj, phone, key)
                else:
                    return Response({
                        'status': False,
                        'detail': 'Sending otp error'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': False,
                'detail': 'Phone number not given in request'
            }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def send_otp_via_sms(old, phone, key):
        conn.request('GET',
                     f'https://2factor.in/API/R1/?module=SMS_OTP&apikey=fffb943c-bc0c-11ed-81b6-0200cd936042&to={phone}&otpvalue={key}&templatenmae=WashForMe')
        res = conn.getresponse()

        data = res.read()
        data = data.decode('utf-8')
        data = ast.literal_eval(data)

        if data['Status'] == 'Success':
            old.otp_session_id = data['Details']
            old.otp = key
            old.save()
            print(f'In validate phone: {old.otp_session_id}, number {phone}')
            return Response({
                'status': True,
                'detail': 'OTP sent successfully'
            })
        else:
            return Response({
                'status': False,
                'detail': 'OTP sending Failed'
            }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def send_otp(phone):
        if phone:
            key = random.randint(999, 9999)
            print(key)
            return key
        else:
            return False


def check_validated(phone, otp_sent):
    old = PhoneOTP.objects.filter(phone__iexact=phone)
    print(old)
    if old.exists():
        old = old.first()
        otp_session_id = old.otp_session_id
        print("In validate otp" + otp_session_id)
        conn.request("GET",
                     "https://2factor.in/API/V1/fffb943c-bc0c-11ed-81b6-0200cd936042/SMS/VERIFY/" + otp_session_id + "/" + otp_sent)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        data = data.decode("utf-8")
        data = ast.literal_eval(data)

        if data["Status"] == 'Success':
            old.validated = True
            old.save()
            return True

        else:
            return False


class ValidateOTP(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone', None)
        otp_sent = request.data.get('otp', None)

        if phone and otp_sent:
            if User.objects.filter(phone__iexact=phone).exists():
                if check_validated(phone, otp_sent):

                    serializer = LoginSerializer(data=request.data)
                    if serializer.is_valid():
                        user = serializer.validated_data['user']
                        login(request, user)
                        return super().post(request, format=None)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({
                        'status': False,
                        'detail': 'OTP INCORRECT'
                    })

            else:
                if check_validated(phone, otp_sent):
                    print(phone)
                    temp_data = {
                        'phone': phone,
                    }
                    serializer = CreateUserSerializer(data=temp_data)
                    if serializer.is_valid():
                        user = serializer.save()
                        user.set_unusable_password()
                        user.save()
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    print(user)
                    serializer = LoginSerializer(data=request.data)
                    if serializer.is_valid():
                        user = serializer.validated_data['user']
                        login(request, user)

                        return super().post(request, format=None)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'status': False,
                        'detail': 'OTP INCORRECT'
                    }, status=status.HTTP_400_BAD_REQUEST)


        else:
            return Response({
                'status': False,
                'detail': 'Please provide both phone and otp for Validation'
            })


class GetUserDetails(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        serializer = UserSerializer(request.user)
        user_data = serializer.data
        user_data['default_address'] = UserAddressSerializerViewOnly(
            UserAddress.objects.filter(user=request.user, current_address=True)[0]).data
        return Response(user_data)

    def put(self, request):
        user = request.user
        user_as_dict = model_to_dict(user)
        new_user_object = request.data
        for key in new_user_object.keys():
            if key in user_as_dict.keys():
                user_as_dict[key] = new_user_object[key]
        serializer = UserSerializer(user, data=user_as_dict)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetWashCategories(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        wash_categories = WashCategory.objects.all()
        serializer = WashCategorySerializer(wash_categories, many=True)
        return Response(serializer.data)


class GetWashItems(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        wash_items = WashItem.objects.all()
        serializer = WashItemSerializer(wash_items, many=True)
        return Response(serializer.data)


class GetWashItemsBasedOnCategory(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request, pk=None):
        try:
            wash_items = WashCategory.objects.get(pk=pk).items
        except WashCategory.DoesNotExist:
            return Response({'error': 'Category Not found'})
        serializer = WashItemSerializer(wash_items, many=True)
        return Response(serializer.data)


class UpdateUser(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def put(request):
        user = request.user


class LogoutUser(KnoxLogoutView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return super().post(request=request)


class WashCategoryItemRelationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, requst):
        data = WashCategoryItemRelation.objects.all()
        serializer = WashCategoryItemRelationSerializer(data, many=True)
        return Response(serializer.data)


class UserWashRelationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserWashRelation.objects.filter(user=request.user)
        serializer = UserWashRelationSerializer(data, many=True)
        return Response(serializer.data)


class CreateUserCategoryItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        user = request.user
        categories_object = [category_object for category_object in request.data]
        wash_category_item_relations = []
        for category_object in categories_object:
            category = WashCategory.objects.get(pk=category_object['category']['id'])
            list_of_items = [WashItem.objects.get(pk=item['id']) for item in category_object['items']]

            wash_category_item_relation = WashCategoryItemRelation.objects.create(
                category=category)
            wash_category_item_relation.items.set(list_of_items)
            wash_category_item_relation.save()
            update_item_count_on_relation_save(sender=WashCategoryItemRelation, instance=wash_category_item_relation,
                                               items_from_api=category_object['items'])
            wash_category_item_relations.append(wash_category_item_relation)

        user_wash_relation = UserWashRelation.objects.create(user=user)
        user_wash_relation.wash_category_relations.set(wash_category_item_relations)

        user_wash_relation.save()
        serializer = UserWashRelationSerializer(user_wash_relation)
        return Response(serializer.data)


# class CreateOrGetSchedulePickUpSlots(APIView):
#     permissions_classes = [IsAuthenticated]
#
#     @staticmethod
#     def get(request):
#         pick_up_schedules = PickUpSchedule.objects.all()
#         today = datetime.datetime.now().date()
#         last_date = today
#         for pick_up_schedule in pick_up_schedules:
#             last_date = pick_up_schedule.date
#             if pick_up_schedule.date < today or (
#                     pick_up_schedule.date == today and pick_up_schedule.end_time < datetime.datetime.now().time()):
#                 pick_up_schedule.make_schedule_completed()
#                 pick_up_schedule.make_unavailable()
#                 pick_up_schedule.save()
#         number_of_days = len(PickUpSchedule.objects.filter(schedule_completed=False))
#         if number_of_days < 7:
#             for i in range(7 - number_of_days):
#                 last_date += datetime.timedelta(days=1)
#                 PickUpSchedule.objects.create(start_time=datetime.time(8, 0, 0), end_time=datetime.time(15, 0, 0),
#                                               available_quota=3, date=last_date)
#         pick_up_schedules = PickUpSchedule.objects.filter(schedule_completed=False)
#         for i in range(len(pick_up_schedules) - 7):
#             last_object = pick_up_schedules.last()
#             pick_up_schedules = pick_up_schedules.exclude(pk=last_object.pk)
#
#         serializer = PickUpScheduleSerializer(pick_up_schedules, many=True)
#         return Response(serializer.data)


class BookTimeSlot(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            user_wash_relation = UserWashRelation.objects.get(pk=request.data['user_wash_relation_id'])
        except UserWashRelation.DoesNotExist:
            return Response({'error': 'User not exists.'}, status=status.HTTP_404_NOT_FOUND)

        pick_up_schedule = self.get_pick_up_schedule(request.data.get('pick_up_slot'))

        if not pick_up_schedule:
            return Response({'error': 'Slot not exists.'}, status=status.HTTP_404_NOT_FOUND)

        if not pick_up_schedule.is_available():
            return Response({'error': 'Selected slot has filled'}, status=status.HTTP_400_BAD_REQUEST)

        slot_book_detail = self.create_slot_book_detail(user, user_wash_relation, pick_up_schedule)

        return Response(SlotBookDetailSerializer(slot_book_detail).data)

    @staticmethod
    def get_pick_up_schedule(pk):
        try:
            return PickUpSchedule.objects.get(pk=pk)
        except PickUpSchedule.DoesNotExist:
            return None

    @staticmethod
    def create_slot_book_detail(user, user_wash_relation, pick_up_schedule):
        pick_up_schedule.filled_quota += 1
        if pick_up_schedule.filled_quota == pick_up_schedule.available_quota:
            pick_up_schedule.make_unavailable()
        pick_up_schedule.save()
        return PickUpSlotBook.objects.create(user=user, pick_up_slot=pick_up_schedule,
                                             user_wash_relation=user_wash_relation)


class CreateOrGetDeliverySlots(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        try:
            pick_up_slot = PickUpSchedule.objects.get(pk=pk)
        except PickUpSchedule.DoesNotExist:
            return Response({'error': 'Pick up slot does not exists.'}, status=status.HTTP_404_NOT_FOUND)

        if pick_up_slot:
            delivery_schedules = DeliverySchedule.objects.all()
            today = datetime.datetime.now().date()
            for delivery_schedule in delivery_schedules:
                if delivery_schedule.date < today or (
                        delivery_schedule.date == today and delivery_schedule.end_time < datetime.datetime.now().time()):
                    delivery_schedule.make_schedule_completed()
                    delivery_schedule.make_unavailable()
                    delivery_schedule.save()

            pick_up_date = pick_up_slot.date
            pick_up_time = pick_up_slot.end_time
            last_date = pick_up_date
            week_days = 7
            delivery_slots = []
            for delivery_schedule in delivery_schedules:
                last_date = delivery_schedule.date
                if delivery_schedule.date > pick_up_date or (
                        delivery_schedule.date == pick_up_date and delivery_schedule.start_time > pick_up_time
                ) and not delivery_schedule.schedule_completed:
                    delivery_slots.append(delivery_schedule)
                    week_days -= 1
                    if week_days == 0:
                        break

            for i in range(week_days):
                last_date += datetime.timedelta(days=1)
                delivery_schedule = DeliverySchedule.objects.create(start_time=datetime.time(8, 0, 0),
                                                                    end_time=datetime.time(15, 0, 0),
                                                                    available_quota=3, date=last_date)
                delivery_slots.append(delivery_schedule)

            serializer = DeliveryScheduleSerializer(delivery_slots, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'Something went wrong.'}, status=status.HTTP_400_BAD_REQUEST)


class BookDeliveryTimeSlot(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            pick_up_slot_detail = PickUpSlotBook.objects.get(pk=request.data['pick_up_slot'])
        except PickUpSlotBook.DoesNotExist:
            return Response({'error': 'Pick up slot does not exists.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            delivery_schedule = DeliverySchedule.objects.get(pk=request.data['delivery_slot'])
        except UserWashRelation.DoesNotExist:
            return Response({'error': 'Delivery slot does not exists.'}, status=status.HTTP_404_NOT_FOUND)

        if pick_up_slot_detail and delivery_schedule:
            if pick_up_slot_detail.pick_up_slot.date >= delivery_schedule.date:
                return Response({'error': 'Delivery slot can not booked before pick up slot.'},
                                status=status.HTTP_400_BAD_REQUEST)
            elif delivery_schedule.schedule_completed:
                return Response({'error': 'Delivery slot date has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            elif not delivery_schedule.is_available():
                return Response({'error': 'Delivery slot was not available.'}, status=status.HTTP_400_BAD_REQUEST)
            else:

                delivery_schedule.filled_quota += 1
                if delivery_schedule.filled_quota == delivery_schedule.available_quota:
                    delivery_schedule.make_unavailable()

                delivery_schedule.save()

                delivery_slot = BookDeliverySlot.objects.create(pick_up_slot=pick_up_slot_detail,
                                                                delivery_slot=delivery_schedule)

                serializer = DeliverySlotBookDetailSerializer(delivery_slot)
                return Response(serializer.data)
        else:
            return Response({'error': 'Something went wrong.'}, status=status.HTTP_400_BAD_REQUEST)


class ChangeCurrentAddress(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk=None):
        try:
            current_address = UserAddress.objects.get(pk=pk, user=request.user)
            old_current_address = UserAddress.objects.get(current_address=True, user=request.user)
            current_address.current_address = True
            old_current_address.current_address = False
            old_current_address.save(update_fields=['current_address'])
            current_address.save(update_fields=['current_address'])
            return Response({'data': 'current address has changed'})
        except UserAddress.DoesNotExist:
            return Response({'error': 'User address not found'})


class AddressHandler(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_addresses = UserAddress.objects.filter(user=request.user)
        serializer = UserAddressSerializer(user_addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        request.data['user'] = UserSerializer(request.user).data
        user_address_object = request.data
        user_address_serializer = UserAddressSerializer(data=user_address_object, context={'request': request})
        if user_address_serializer.is_valid():
            user_address_serializer.save()
            return Response(user_address_serializer.data)
        else:
            return Response(user_address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        old_user_address_object = UserAddress.objects.get(pk=pk)
        user_address_object = request.data
        user_address_object = UserAddressSerializer(old_user_address_object, data=user_address_object)
        if user_address_object.is_valid():
            user_address_object.save()
            return Response(user_address_object.data)
        else:
            return Response(user_address_object.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        try:
            user_address_object = UserAddress.objects.get(pk=pk)
            user_address_object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserAddress.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

