import apiClient from './client';
import {
  User, Product, ProductCategory, Cart, Order, Review,
  B2BQuote, CompanyAddress, BulkOrderDiscount, ApiResponse,
  UserType
} from '../types';

export const AuthService = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/token/', { username, password });
    return response.data;
  },
  register: async (userData: any) => {
    const response = await apiClient.post('/register/', userData);
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

export const UserService = {
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get('/users/me/');
    return response.data;
  },
  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch('/users/me/', data);
    return response.data;
  },
  requestB2BVerification: async (): Promise<void> => {
    await apiClient.post('/users/me/request_verification/');
  },
};

export const ProductService = {
  getProducts: async (params?: any): Promise<ApiResponse<Product>> => {
    const response = await apiClient.get('/products/', { params });
    return response.data;
  },
  getProduct: async (id: number): Promise<Product> => {
    const response = await apiClient.get(`/products/${id}/`);
    return response.data;
  },
  getFeatured: async (): Promise<Product[]> => {
    const response = await apiClient.get('/products/?is_featured=true');
    return response.data.results;
  },
  getCategories: async (): Promise<ProductCategory[]> => {
    const response = await apiClient.get('/categories/');
    return response.data.results;
  },
};

export const CartService = {
  getCart: async (): Promise<Cart> => {
    const response = await apiClient.get('/cart/my_cart/');
    return response.data;
  },
  addItem: async (productId: number, quantity: number, variantId?: number): Promise<Cart> => {
    const response = await apiClient.post('/cart/add_item/', {
      product_id: productId,
      variant_id: variantId,
      quantity,
    });
    return response.data;
  },
  updateItem: async (itemId: number, quantity: number): Promise<Cart> => {
    const response = await apiClient.post('/cart/update_item/', {
      item_id: itemId,
      quantity,
    });
    return response.data;
  },
  clearCart: async (): Promise<void> => {
    await apiClient.post('/cart/clear_cart/');
  },
  switchToB2B: async (): Promise<void> => {
    await apiClient.post('/cart/switch_to_b2b/');
  },
};

export const OrderService = {
  getOrders: async (params?: any): Promise<ApiResponse<Order>> => {
    const response = await apiClient.get('/orders/', { params });
    return response.data;
  },
  getOrder: async (id: number): Promise<Order> => {
    const response = await apiClient.get(`/orders/${id}/`);
    return response.data;
  },
  createOrder: async (orderData: any): Promise<Order> => {
    const response = await apiClient.post('/orders/create_order/', orderData);
    return response.data;
  },
  cancelOrder: async (id: number): Promise<void> => {
    await apiClient.post(`/orders/${id}/cancel/`);
  },
};

export const QuoteService = {
  getQuotes: async (): Promise<ApiResponse<B2BQuote>> => {
    const response = await apiClient.get('/quotes/');
    return response.data;
  },
  createQuote: async (data: { product_id: number; quantity: number; requested_price: number; notes?: string }): Promise<B2BQuote> => {
    const response = await apiClient.post('/quotes/', data);
    return response.data;
  },
};

export const AddressService = {
  getAddresses: async (): Promise<CompanyAddress[]> => {
    const response = await apiClient.get('/addresses/');
    return response.data.results;
  },
  createAddress: async (data: any): Promise<CompanyAddress> => {
    const response = await apiClient.post('/addresses/', data);
    return response.data;
  },
  setDefaultAddress: async (id: number): Promise<void> => {
    await apiClient.post(`/addresses/${id}/set_default/`);
  },
};

export const DiscountService = {
  getApplicableDiscounts: async (): Promise<BulkOrderDiscount[]> => {
    const response = await apiClient.get('/discounts/applicable_discounts/');
    return response.data;
  },
};