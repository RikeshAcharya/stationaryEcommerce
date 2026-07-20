// User Types
export enum UserType {
  B2C = 'b2c',
  B2B = 'b2b',
}

export interface User {
  id: number;
  username: string;
  email: string;
  user_type: UserType;
  company_name?: string;
  business_registration_number?: string;
  tax_id?: string;
  phone_number: string;
  is_verified: boolean;
  is_vip: boolean;
  credit_limit: number;
  first_name: string;
  last_name: string;
  created_at: string;
}

// Product Types
export interface ProductCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  image?: string;
  parent?: number;
  children?: ProductCategory[];
  product_count: number;
  is_active: boolean;
}

export interface ProductImage {
  id: number;
  image: string;
  is_primary: boolean;
  alt_text: string;
}

export interface ProductVariant {
  id: number;
  name: string;
  value: string;
  retail_price_adjustment: number;
  wholesale_price_adjustment: number;
  stock: number;
  sku: string;
}

export interface BulkDiscountTier {
  min_qty: number;
  discount: number;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  sku: string;
  brand: string;
  price: number; // Dynamic based on user type
  retail_price: number;
  wholesale_price: number;
  wholesale_price_display: number;
  wholesale_min_quantity: number;
  bulk_discount_tiers: BulkDiscountTier[];
  stock: number;
  low_stock_threshold: number;
  weight_grams: number;
  dimensions: string;
  category: number;
  category_name: string;
  is_active: boolean;
  is_featured: boolean;
  average_rating: number;
  total_reviews: number;
  images: ProductImage[];
  variants: ProductVariant[];
  created_at: string;
  updated_at: string;
}

// Cart Types
export interface CartItem {
  id: number;
  product: Product;
  variant?: ProductVariant;
  quantity: number;
  price: number;
  total_price: number;
}

export interface Cart {
  id: number;
  items: CartItem[];
  total_price: number;
  item_count: number;
  is_b2b_order: boolean;
  created_at: string;
  updated_at: string;
}

// Order Types
export interface OrderItem {
  id: number;
  product: number;
  product_name: string;
  product_sku: string;
  variant?: ProductVariant;
  quantity: number;
  price: number;
  total: number;
}

export interface Order {
  id: number;
  order_number: string;
  order_type: 'b2c' | 'b2b';
  order_type_display: string;
  user: User;
  status: 'pending' | 'processing' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  status_display: string;
  total_amount: number;
  purchase_order_number?: string;
  delivery_instructions: string;
  require_signature: boolean;
  shipping_address: string;
  shipping_city: string;
  shipping_state: string;
  shipping_zip: string;
  shipping_country: string;
  payment_method: string;
  payment_status: string;
  payment_reference: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
  expected_delivery_date?: string;
}

// Review Types
export interface Review {
  id: number;
  product: number;
  user: User;
  rating: number;
  comment: string;
  is_verified_purchase: boolean;
  created_at: string;
  updated_at: string;
}

// B2B Quote Types
export interface B2BQuote {
  id: number;
  user: User;
  product: Product;
  quantity: number;
  requested_price: number;
  offered_price?: number;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  notes: string;
  created_at: string;
  updated_at: string;
}

// Company Address
export interface CompanyAddress {
  id: number;
  user: number;
  address_type: 'billing' | 'shipping' | 'both';
  company_name: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  is_default: boolean;
  contact_person: string;
  contact_phone: string;
}

// Bulk Discount
export interface BulkOrderDiscount {
  id: number;
  name: string;
  min_order_value: number;
  discount_percentage: number;
  is_active: boolean;
  valid_from: string;
  valid_to: string;
}

// API Response
export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}