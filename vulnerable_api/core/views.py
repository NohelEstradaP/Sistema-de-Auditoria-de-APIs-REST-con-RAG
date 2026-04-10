from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Product, Order
from .serializers import UserSerializer, ProductSerializer, OrderSerializer


# VULNERABILIDAD API2: sin permission_classes ni authentication_classes
# Cualquier usuario puede listar todos los usuarios con sus datos sensibles
class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# VULNERABILIDAD API2 + API3: sin autenticación y expone datos sensibles
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# VULNERABILIDAD API1 (BOLA): no verifica que la orden pertenece al usuario autenticado
# Un usuario puede acceder a /api/orders/2/ aunque la orden sea de otro usuario
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


# VULNERABILIDAD API1 + API4: sin autenticación y sin throttling
# Cualquiera puede listar TODAS las órdenes de todos los usuarios
class OrderListView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


# VULNERABILIDAD API5: endpoint de administración sin verificación de rol
# Cualquier usuario autenticado (o sin autenticar) puede acceder
class AdminPanelView(APIView):
    def get(self, request):
        users = User.objects.values('id', 'username', 'email', 'is_admin', 'password')
        return Response({'admin_data': list(users)})

    def delete(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
