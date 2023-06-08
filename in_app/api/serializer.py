from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

from in_app.models import (
    PhoneOTP,
    WashCategory,
    WashItem,
    WashCategoryItemRelation,
    UserWashRelation,
    PickUpSchedule,
    PickUpSlotBook,
    DeliverySchedule,
    BookDeliverySlot,
    Address,
    AddressType,
    UserAddress
)

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('phone',)

        # extra_kwargs = {'password': {'write_only': True}, }

        def create(self, validated_data):
            user = User.objects.create(**validated_data)
            return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'phone', 'email', 'other_details')


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField(
        style={'input_type': 'otp'}, trim_whitespace=False
    )

    def validate(self, data):
        print(data)
        phone = data.get('phone')
        otp = data.get('otp')

        if phone and otp:
            if User.objects.filter(phone=phone).exists():
                phoneOTP = PhoneOTP.objects.get(phone=phone)
                print(phone, otp)
                user = None
                if otp == phoneOTP.otp:
                    user = User.objects.get(phone=phone)
                    phoneOTP.delete()
            else:
                msg = {
                    'detail': 'Phone number not found',
                    'status': False,
                }
                raise serializers.ValidationError(msg)

            if not user:
                msg = {
                    'detail': 'Phone and otp not matching. Try again',
                    'status': False,
                }
                raise serializers.ValidationError(msg, code='authorization')


        else:
            msg = {
                'detail': 'Phone number and otp not found in request',
                'status': False,
            }
            raise serializers.ValidationError(msg, code='authorization')

        data['user'] = user
        return data


class WashCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WashCategory
        exclude = ['items']


class WashItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WashItem
        fields = "__all__"


class WashCategoryItemRelationSerializer(serializers.ModelSerializer):
    category = WashCategorySerializer()

    class Meta:
        model = WashCategoryItemRelation
        fields = '__all__'
        depth = 1


class UserWashRelationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    wash_category_relations = WashCategoryItemRelationSerializer(many=True)

    class Meta:
        model = UserWashRelation
        fields = '__all__'
        depth = 3


# class CreateUserWashCategoryItemRelationSerializer(serializers.ModelSerializer):
#     user = serializers.CharField()
#     wash_category_relation = serializers.JSONField()
#     items = serializers.JSONField()
#
#     class Meta:
#         model = UserWashRelation
#         fields = '__all__'
#         depth = 1
#
#     def validate(self, validated_data):
#         category = WashCategory.objects.get(pk=validated_data['wash_category_relation'])
#         list_of_items = [WashItem.objects.get(pk=item) for item in validated_data['items']]
#         user = User.objects.get(pk=validated_data['user'])
#
#         wash_category_item_relation = WashCategoryItemRelation.objects.create(
#             category=category)
#         wash_category_item_relation.items.set(list_of_items)
#
#         user_wash_relation = UserWashRelation.objects.create(user=user,
#                                                              wash_category_relation=wash_category_item_relation)
#
#         wash_category_item_relation.save()
#         user_wash_relation.save()
#
#         return validated_data


class PickUpScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickUpSchedule
        fields = '__all__'


class SlotBookDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = PickUpSlotBook
        fields = '__all__'
        depth = 1


class DeliveryScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverySchedule
        fields = '__all__'


class DeliverySlotBookDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookDeliverySlot
        fields = '__all__'
        depth = 1


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class AddressTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressType
        fields = '__all__'


class UserAddressSerializerViewOnly(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'address', 'address_type']
        depth = 1


class UserAddressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    address = AddressSerializer()
    address_type = AddressTypeSerializer()

    class Meta:
        model = UserAddress
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        user = self.context['request'].user
        address_data = validated_data.pop('address')
        address_type_data = validated_data.pop('address_type')

        # Create the Address object
        address_serializer = AddressSerializer(data=address_data)
        address_serializer.is_valid(raise_exception=True)
        address = address_serializer.save()

        # Create the AddressType object
        address_type_serializer = AddressTypeSerializer(data=address_type_data)
        address_type_serializer.is_valid(raise_exception=True)
        address_type = address_type_serializer.save()

        # Create the UserAddress object
        user_address = UserAddress.objects.create(
            user=user,
            address=address,
            address_type=address_type,
            **validated_data
        )

        return user_address

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        address_type_data = validated_data.pop('address_type', None)

        if address_data:
            address = instance.address
            address_serializer = AddressSerializer(address, data=address_data)
            address_serializer.is_valid(raise_exception=True)
            address_serializer.save()

        if address_type_data:
            # Update the AddressType object
            address_type = instance.address_type
            address_type_serializer = AddressTypeSerializer(address_type, data=address_type_data)
            address_type_serializer.is_valid(raise_exception=True)
            address_type_serializer.save()

        # Update the UserAddress object
        instance = super(UserAddressSerializer, self).update(instance, validated_data)

        return instance


