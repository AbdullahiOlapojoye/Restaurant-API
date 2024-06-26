from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from .models import MenuItem, Cart, Order, OrderItem, Category
from django.utils.timezone import timezone
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, UserSerializer, CategorySerializer

class CustomUserRateThrottle(throttling.UserRateThrottle):
    rate = '5/minute'  # Custom rate for specific view

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Delivery crew').exists()

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

class MenuItemListView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']
    ordering_fields = ['price']
    throttle_classes = [CustomUserRateThrottle]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsManager()]

class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [CustomUserRateThrottle]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsManager()]

class CartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request):
        menu_item_id = request.data.get('menu_item_id')
        quantity = request.data.get('quantity', 1)
        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
            unit_price = menu_item.price
            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                menu_item=menu_item,
                defaults={'quantity': quantity, 'unit_price': unit_price, 'price': unit_price * quantity}
            )
            if not created:
                cart_item.quantity += int(quantity)
                cart_item.price = cart_item.unit_price * cart_item.quantity
                cart_item.save()
            return Response(CartSerializer(cart_item).data, status=201)
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found"}, status=404)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=204)

class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        if self.request.user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        cart_items = Cart.objects.filter(user=self.request.user)
        order = serializer.save(user=self.request.user, date=timezone.now(), total=sum(item.price for item in cart_items))
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=item.menu_item,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )
        cart_items.delete()

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        elif self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), IsManager()]
        elif self.request.method in ['PUT', 'PATCH']:
            if self.request.user.groups.filter(name='Manager').exists():
                return [permissions.IsAuthenticated(), IsManager()]
            if self.request.user.groups.filter(name='Delivery crew').exists():
                return [permissions.IsAuthenticated(), IsDeliveryCrew()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        order = get_object_or_404(Order, id=self.kwargs['pk'])
        if self.request.user.groups.filter(name='Manager').exists() or self.request.user == order.user or self.request.user == order.delivery_crew:
            return order
        else:
            raise PermissionDenied()

class UserGroupListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsManager]
    throttle_classes = [CustomUserRateThrottle]

    def get_queryset(self):
        group_name = self.kwargs['group_name']
        return User.objects.filter(groups__name=group_name)

class AddUserToGroupView(APIView):
    permission_classes = [IsManager]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        group_name = self.kwargs['group_name']
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            return Response(status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

class RemoveUserFromGroupView(APIView):
    permission_classes = [IsManager]
    throttle_classes = [CustomUserRateThrottle]

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        group_name = self.kwargs['group_name']
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name=group_name)
            user.groups.remove(group)
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)