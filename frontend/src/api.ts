export type PlatformName = "swiggy" | "zomato" | "google";

export type OperatingHours = {
  is_open_now: boolean;
  weekday_text: string[];
  opens_at?: string | null;
  closes_at?: string | null;
};

export type PlatformListing = {
  platform: PlatformName;
  restaurant_id?: string | null;
  name: string;
  cuisine: string[];
  rating?: number | null;
  rating_count?: number | null;
  delivery_time_minutes?: number | null;
  delivery_fee?: number | null;
  minimum_order?: number | null;
  discount_label?: string | null;
  deep_link?: string | null;
  operating_hours?: OperatingHours | null;
  image_url?: string | null;
};

export type UnifiedRestaurant = {
  name: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  google_place_id?: string | null;
  swiggy?: PlatformListing | null;
  zomato?: PlatformListing | null;
  cheaper_platform?: PlatformName | null;
  estimated_saving?: number | null;
};

export type MenuItem = {
  id?: string | null;
  name: string;
  category: string;
  price: number;
  is_veg: boolean;
  is_popular: boolean;
  platform: PlatformName;
};

export type RestaurantMenuResponse = {
  restaurant_name: string;
  google_place_id?: string | null;
  source: string;
  last_updated?: string | null;
  disclaimer?: string | null;
  items: MenuItem[];
};

export type ProviderSummary = {
  id: "swiggy" | "zomato";
  name: string;
  mode: string;
};

export type CartItemRequest = {
  menu_item_id: string;
  quantity: number;
};

export type CartQuote = {
  provider_id: "swiggy" | "zomato";
  provider_name: string;
  currency: "INR";
  eta_minutes: number;
  line_items: Array<{
    menu_item_id: string;
    name: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }>;
  subtotal: number;
  discount: number;
  taxes: number;
  delivery_fee: number;
  platform_fee: number;
  total: number;
};

export type CartCompareResponse = {
  winner?: CartQuote | null;
  quotes: CartQuote[];
};

export type CompareResponse = {
  query: string;
  location: {
    lat: number;
    lng: number;
    radius_meters: number;
  };
  cached: boolean;
  total_results: number;
  results: UnifiedRestaurant[];
};

export type LocationLookupResponse = {
  pincode: string;
  latitude: number;
  longitude: number;
  formatted_address: string;
  source: string;
};

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "https://foodduel.onrender.com";

export function apiAssetUrl(path?: string | null) {
  if (!path) {
    return "";
  }

  if (path.startsWith("/api")) {
    return `${apiBase}${path}`;
  }

  return path;
}

export async function compareRestaurants(params: {
  query: string;
  lat: number;
  lng: number;
  radius: number;
}): Promise<CompareResponse> {
  const search = new URLSearchParams({
    query: params.query,
    lat: String(params.lat),
    lng: String(params.lng),
    radius: String(params.radius),
    nocache: "true"
  });

  const response = await fetch(`${apiBase}/api/compare?${search.toString()}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    const message = response.status === 422
      ? "Check the search and location values."
      : "FoodDuel could not fetch restaurants right now.";
    throw new Error(message);
  }

  return response.json();
}

export async function lookupPincode(pincode: string): Promise<LocationLookupResponse> {
  const response = await fetch(`${apiBase}/api/location/pincode/${pincode}`);

  if (!response.ok) {
    const message = response.status === 404
      ? "We could not find that PIN code yet."
      : "FoodDuel could not check that PIN code right now.";
    throw new Error(message);
  }

  return response.json();
}

export async function fetchRestaurantMenu(params: {
  placeId?: string | null;
  restaurantName: string;
  query: string;
}): Promise<RestaurantMenuResponse> {
  const search = new URLSearchParams({
    restaurant_name: params.restaurantName,
    query: params.query
  });

  if (params.placeId) {
    search.set("place_id", params.placeId);
  }

  const response = await fetch(`${apiBase}/api/restaurants/menu?${search.toString()}`);

  if (!response.ok) {
    throw new Error("FoodDuel could not fetch this menu right now.");
  }

  return response.json();
}

export async function fetchProviders(): Promise<ProviderSummary[]> {
  const response = await fetch(`${apiBase}/api/providers`);

  if (!response.ok) {
    throw new Error("FoodDuel could not fetch providers right now.");
  }

  return response.json();
}

export async function fetchProviderMenu(params: {
  providerId: "swiggy" | "zomato";
  restaurantId: string;
}): Promise<RestaurantMenuResponse> {
  const response = await fetch(
    `${apiBase}/api/providers/${params.providerId}/restaurants/${params.restaurantId}/menu`
  );

  if (!response.ok) {
    throw new Error("FoodDuel could not fetch this provider menu right now.");
  }

  return response.json();
}

export async function compareCart(params: {
  items: CartItemRequest[];
  latitude?: number;
  longitude?: number;
}): Promise<CartCompareResponse> {
  const response = await fetch(`${apiBase}/api/cart/compare`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(params)
  });

  if (!response.ok) {
    throw new Error("FoodDuel could not compare this cart right now.");
  }

  return response.json();
}
