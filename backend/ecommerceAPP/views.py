from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Avg, F
from django.utils import timezone
from decimal import Decimal
import uuid
from .models import *
from .serializers import *
from .permissions import *

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset for product categories (supports B2B & B2C).
    """
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Admin can see all, others only active
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
        
class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset for product categories (supports B2B & B2C).
    """
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show active categories, but admin can see all
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
        
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrB2BOwner]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'company_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Regular users can only see themselves
            queryset = queryset.filter(id=self.request.user.id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def verify_b2b(self, request, pk=None):
        """Admin endpoint to verify B2B users"""
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        user.is_verified = True
        user.save()
        return Response({'status': 'B2B user verified'})

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'is_active', 'brand']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['retail_price', 'wholesale_price', 'created_at', 'average_rating']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Price range filters
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(retail_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(retail_price__lte=max_price)
        
        # B2B specific filters
        if self.request.user.is_authenticated and self.request.user.user_type == UserType.B2B:
            # Show wholesale pricing
            queryset = queryset.annotate(
                display_price=F('wholesale_price')
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        product = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user has purchased this product
            has_purchased = Order.objects.filter(
                user=request.user,
                items__product=product,
                status='delivered'
            ).exists()
            
            review = serializer.save(
                product=product,
                user=request.user,
                is_verified_purchase=has_purchased
            )
            
            # Update product ratings
            reviews = product.reviews.all()
            product.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            product.total_reviews = reviews.count()
            product.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    
    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_cart(request.user)
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if B2B minimum quantity
        if request.user.user_type == UserType.B2B:
            if quantity < product.wholesale_min_quantity:
                return Response({
                    'error': f'Minimum quantity for wholesale is {product.wholesale_min_quantity}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check stock
        if product.stock < quantity:
            return Response({'error': 'Insufficient stock'}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant_id=variant_id,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        cart = self.get_cart(request.user)
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 0))
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if quantity <= 0:
            cart_item.delete()
        else:
            # Check stock
            if cart_item.product.stock < quantity:
                return Response({'error': 'Insufficient stock'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        cart = self.get_cart(request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'})
    
    @action(detail=False, methods=['post'])
    def switch_to_b2b(self, request):
        """Switch cart to B2B mode"""
        cart = self.get_cart(request.user)
        if request.user.user_type != UserType.B2B:
            return Response({'error': 'User is not B2B'}, status=status.HTTP_400_BAD_REQUEST)
        cart.is_b2b_order = True
        cart.save()
        return Response({'message': 'Switched to B2B mode'})

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'purchase_order_number']
    ordering_fields = ['created_at', 'total_amount', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by order type
        order_type = self.request.query_params.get('order_type')
        if order_type:
            queryset = queryset.filter(order_type=order_type)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate B2B minimum order
        if request.user.user_type == UserType.B2B and not cart.is_b2b_order:
            return Response({'error': 'Please switch to B2B mode'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate order number
        order_type_prefix = 'B2B' if cart.is_b2b_order else 'B2C'
        order_number = f"{order_type_prefix}-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate total
        total = cart.get_total_price()
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            order_type='b2b' if cart.is_b2b_order else 'b2c',
            total_amount=total,
            shipping_address=request.data.get('shipping_address'),
            shipping_city=request.data.get('shipping_city'),
            shipping_state=request.data.get('shipping_state'),
            shipping_zip=request.data.get('shipping_zip'),
            shipping_country=request.data.get('shipping_country'),
            payment_method=request.data.get('payment_method'),
            purchase_order_number=request.data.get('purchase_order_number'),
            delivery_instructions=request.data.get('delivery_instructions'),
            require_signature=request.data.get('require_signature', False),
            expected_delivery_date=request.data.get('expected_delivery_date')
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=cart_item.get_price(),
                total=cart_item.get_total_price()
            )
        
        # Clear cart
        cart.items.all().delete()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Admin endpoint to update order status"""
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        return Response({'status': 'Order status updated'})

class B2BQuoteViewSet(viewsets.ModelViewSet):
    queryset = B2BQuote.objects.all()
    serializer_class = B2BQuoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product__name', 'notes']
    ordering_fields = ['created_at', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == UserType.B2B:
            queryset = queryset.filter(user=self.request.user)
        elif self.request.user.is_staff:
            queryset = queryset.all()
        else:
            queryset = queryset.none()
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # If B2B, require verification
        if user.user_type == UserType.B2B:
            user.is_verified = False
            user.save()
        
        return Response({
            'user': CustomUserSerializer(user).data,
            'message': 'Registration successful. Please log in.'
        }, status=status.HTTP_201_CREATED)

class CompanyAddressViewSet(viewsets.ModelViewSet):
    queryset = CompanyAddress.objects.all()
    serializer_class = CompanyAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        # Reset all addresses for this user
        CompanyAddress.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address set'})

class BulkOrderDiscountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BulkOrderDiscount.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now()
    )
    serializer_class = BulkOrderDiscountSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def applicable_discounts(self, request):
        """Get discounts applicable to current cart"""
        cart = Cart.objects.get(user=request.user)
        total = cart.get_total_price()
        
        discounts = self.get_queryset().filter(min_order_value__lte=total)
        serializer = self.get_serializer(discounts, many=True)
        return Response(serializer.data)

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def sales_overview(self, request):
        """Get sales overview for admin dashboard"""
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
        
        b2b_orders = Order.objects.filter(order_type='b2b').count()
        b2b_revenue = Order.objects.filter(order_type='b2b').aggregate(total=Sum('total_amount'))['total'] or 0
        
        b2c_orders = Order.objects.filter(order_type='b2c').count()
        b2c_revenue = Order.objects.filter(order_type='b2c').aggregate(total=Sum('total_amount'))['total'] or 0
        
        return Response({
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'b2b': {
                'orders': b2b_orders,
                'revenue': b2b_revenue,
                'percentage': (b2b_revenue / total_revenue * 100) if total_revenue > 0 else 0
            },
            'b2c': {
                'orders': b2c_orders,
                'revenue': b2c_revenue,
                'percentage': (b2c_revenue / total_revenue * 100) if total_revenue > 0 else 0
            }
        })
    
    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """Get top selling products"""
        from django.db.models import Count, Sum
        
        top_products = OrderItem.objects.values(
            'product__id', 'product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total')
        ).order_by('-total_sold')[:10]
        
        return Response(top_products)