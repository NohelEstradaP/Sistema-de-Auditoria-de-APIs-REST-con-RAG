from rest_framework import serializers
from .models import User, Product, Order


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # VULNERABILIDAD API3: expone password hash e is_admin sin read_only
        fields = ['id', 'username', 'email', 'password', 'is_admin', 'is_staff']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        # VULNERABILIDAD API3: owner es escribible — cualquier usuario puede
        # crear una orden en nombre de otro usuario (mass assignment)
        fields = '__all__'
