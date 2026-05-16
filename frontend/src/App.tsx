import { FormEvent, useMemo, useState } from "react";
import {
  ArrowRight,
  Clock3,
  ChevronDown,
  ChevronUp,
  IndianRupee,
  LocateFixed,
  Loader2,
  MapPin,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Utensils
} from "lucide-react";
import {
  apiAssetUrl,
  compareRestaurants,
  fetchRestaurantMenu,
  lookupPincode,
  PlatformListing,
  RestaurantMenuResponse,
  UnifiedRestaurant
} from "./api";

type LocationMode = "pincode" | "live";

type FormState = {
  query: string;
  pincode: string;
  radius: string;
};

type SearchLocation = {
  lat: number;
  lng: number;
  label: string;
};

const defaultForm: FormState = {
  query: "biryani",
  pincode: "500081",
  radius: "3000"
};

type CuisineCategory = "indian" | "global" | "snack" | "drink" | "dessert" | "healthy";

const cuisineImages: Record<CuisineCategory, string> = {
  indian: "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=500&q=80",
  global: "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=500&q=80",
  snack: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=80",
  drink: "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=500&q=80",
  dessert: "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=500&q=80",
  healthy: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=500&q=80"
};

const foodChoices: Array<{ label: string; query: string; category: CuisineCategory }> = [
  { label: "Biryani", query: "biryani", category: "indian" },
  { label: "Pizza", query: "pizza", category: "global" },
  { label: "Burgers", query: "burger", category: "snack" },
  { label: "Momos", query: "momos", category: "snack" },
  { label: "Dosa", query: "dosa", category: "indian" },
  { label: "Desserts", query: "dessert", category: "dessert" },
  { label: "North Indian", query: "north indian", category: "indian" },
  { label: "South Indian", query: "south indian", category: "indian" },
  { label: "Andhra Meals", query: "andhra meals", category: "indian" },
  { label: "Hyderabadi", query: "hyderabadi", category: "indian" },
  { label: "Mughlai", query: "mughlai", category: "indian" },
  { label: "Tandoori", query: "tandoori", category: "indian" },
  { label: "Kebabs", query: "kebabs", category: "indian" },
  { label: "Paratha", query: "paratha", category: "indian" },
  { label: "Thali", query: "thali", category: "indian" },
  { label: "Pure Veg", query: "pure veg", category: "healthy" },
  { label: "Breakfast", query: "breakfast", category: "indian" },
  { label: "Idli", query: "idli", category: "indian" },
  { label: "Vada", query: "vada", category: "snack" },
  { label: "Puri", query: "puri", category: "indian" },
  { label: "Pulao", query: "pulao", category: "indian" },
  { label: "Fried Rice", query: "fried rice", category: "global" },
  { label: "Chinese", query: "chinese", category: "global" },
  { label: "Noodles", query: "noodles", category: "global" },
  { label: "Manchurian", query: "manchurian", category: "global" },
  { label: "Thai", query: "thai", category: "global" },
  { label: "Japanese", query: "japanese", category: "global" },
  { label: "Sushi", query: "sushi", category: "global" },
  { label: "Korean", query: "korean", category: "global" },
  { label: "Italian", query: "italian", category: "global" },
  { label: "Pasta", query: "pasta", category: "global" },
  { label: "Mexican", query: "mexican", category: "global" },
  { label: "Mediterranean", query: "mediterranean", category: "global" },
  { label: "Lebanese", query: "lebanese", category: "global" },
  { label: "Arabian", query: "arabian", category: "global" },
  { label: "Shawarma", query: "shawarma", category: "snack" },
  { label: "Rolls", query: "rolls", category: "snack" },
  { label: "Sandwiches", query: "sandwich", category: "snack" },
  { label: "Wraps", query: "wraps", category: "snack" },
  { label: "Street Food", query: "street food", category: "snack" },
  { label: "Chaat", query: "chaat", category: "snack" },
  { label: "Pav Bhaji", query: "pav bhaji", category: "snack" },
  { label: "Samosa", query: "samosa", category: "snack" },
  { label: "Bakery", query: "bakery", category: "dessert" },
  { label: "Cakes", query: "cakes", category: "dessert" },
  { label: "Ice Cream", query: "ice cream", category: "dessert" },
  { label: "Waffles", query: "waffles", category: "dessert" },
  { label: "Donuts", query: "donuts", category: "dessert" },
  { label: "Mithai", query: "mithai", category: "dessert" },
  { label: "Tea", query: "tea", category: "drink" },
  { label: "Coffee", query: "coffee", category: "drink" },
  { label: "Juices", query: "juice", category: "drink" },
  { label: "Milkshakes", query: "milkshake", category: "drink" },
  { label: "Smoothies", query: "smoothie", category: "drink" },
  { label: "Salads", query: "salad", category: "healthy" },
  { label: "Healthy Bowls", query: "healthy bowl", category: "healthy" },
  { label: "Protein Meals", query: "protein meals", category: "healthy" },
  { label: "Continental", query: "continental", category: "global" },
  { label: "Seafood", query: "seafood", category: "global" },
  { label: "Barbecue", query: "barbecue", category: "global" },
  { label: "Steak", query: "steak", category: "global" },
  { label: "Fast Food", query: "fast food", category: "snack" },
  { label: "Cloud Kitchen", query: "cloud kitchen", category: "global" }
];

const featuredImage =
  "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=1200&q=80";

function App() {
  const [form, setForm] = useState<FormState>(defaultForm);
  const [results, setResults] = useState<UnifiedRestaurant[]>([]);
  const [cached, setCached] = useState(false);
  const [searchedQuery, setSearchedQuery] = useState("");
  const [locationMode, setLocationMode] = useState<LocationMode>("pincode");
  const [liveLocation, setLiveLocation] = useState<SearchLocation | null>(null);
  const [activeLocation, setActiveLocation] = useState<SearchLocation | null>(null);
  const [cuisineSearch, setCuisineSearch] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [openMenuKey, setOpenMenuKey] = useState("");
  const [menuByKey, setMenuByKey] = useState<Record<string, RestaurantMenuResponse>>({});
  const [menuLoadingKey, setMenuLoadingKey] = useState("");
  const [menuError, setMenuError] = useState("");

  const locationLabel = useMemo(() => {
    if (activeLocation) {
      return formatLocationLabel(activeLocation.label);
    }

    if (locationMode === "live") {
      return liveLocation ? formatLocationLabel(liveLocation.label) : "your live location";
    }

    return form.pincode.length === 6 ? `PIN ${form.pincode}` : "your selected location";
  }, [activeLocation, form.pincode, liveLocation, locationMode]);

  const resultSummary = useMemo(() => {
    if (!searchedQuery) {
      return `Start with a dish, restaurant, or craving near ${locationLabel}.`;
    }

    if (results.length === 0) {
      return `No restaurants found for ${searchedQuery} near ${locationLabel}.`;
    }

    return `${results.length} places found for ${searchedQuery} near ${locationLabel}`;
  }, [locationLabel, results.length, searchedQuery]);

  const visibleCuisines = useMemo(() => {
    const search = cuisineSearch.trim().toLowerCase();
    const filtered = search
      ? foodChoices.filter((choice) => (
          choice.label.toLowerCase().includes(search) ||
          choice.query.toLowerCase().includes(search) ||
          choice.category.includes(search)
        ))
      : foodChoices;

    const visible = filtered.slice(0, 12);
    const selected = foodChoices.find((choice) => choice.query === form.query);
    if (selected && !visible.some((choice) => choice.query === selected.query)) {
      return [selected, ...visible.slice(0, 11)];
    }

    return visible;
  }, [cuisineSearch, form.query]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runCompare(form.query);
  }

  async function runCompare(query: string) {
    setError("");
    setIsLoading(true);
    const cleanQuery = query.trim();
    if (!cleanQuery) {
      setError("Choose a food type or enter a restaurant name.");
      setIsLoading(false);
      return;
    }

    try {
      const location = await resolveSearchLocation();
      const data = await compareRestaurants({
        query: cleanQuery,
        lat: location.lat,
        lng: location.lng,
        radius: Number(form.radius)
      });

      setResults(data.results);
      setCached(data.cached);
      setSearchedQuery(data.query);
      setActiveLocation(location);
      setOpenMenuKey("");
      setMenuError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }

  async function toggleRestaurantMenu(restaurant: UnifiedRestaurant) {
    const menuKey = restaurant.google_place_id || `${restaurant.name}-${restaurant.address || ""}`;
    setMenuError("");

    if (openMenuKey === menuKey) {
      setOpenMenuKey("");
      return;
    }

    setOpenMenuKey(menuKey);
    if (menuByKey[menuKey]) {
      return;
    }

    setMenuLoadingKey(menuKey);
    try {
      const menu = await fetchRestaurantMenu({
        placeId: restaurant.google_place_id,
        restaurantName: restaurant.name,
        query: searchedQuery || form.query
      });
      setMenuByKey((current) => ({ ...current, [menuKey]: menu }));
    } catch (err) {
      setMenuError(err instanceof Error ? err.message : "Could not fetch menu.");
    } finally {
      setMenuLoadingKey("");
    }
  }

  async function selectFood(query: string) {
    setForm((current) => ({ ...current, query }));
    await runCompare(query);
  }

  function cuisinePhotoUrl(choice: { query: string; category: CuisineCategory }) {
    const params = new URLSearchParams({
      query: choice.query,
      radius: form.radius,
      maxwidth: "500"
    });

    if (locationMode === "live" && liveLocation) {
      params.set("lat", String(liveLocation.lat));
      params.set("lng", String(liveLocation.lng));
    } else if (form.pincode.length === 6) {
      params.set("pincode", form.pincode);
    } else {
      return cuisineImages[choice.category];
    }

    return apiAssetUrl(`/api/photos/cuisine?${params.toString()}`);
  }

  async function resolveSearchLocation() {
    if (locationMode === "live") {
      if (!liveLocation) {
        return requestLiveLocation();
      }

      return liveLocation;
    }

    const lookup = await lookupPincode(form.pincode.trim());
    return {
      lat: lookup.latitude,
      lng: lookup.longitude,
      label: lookup.formatted_address
    };
  }

  async function requestLiveLocation() {
    if (!("geolocation" in navigator)) {
      throw new Error("Live location is not available in this browser.");
    }

    setIsLocating(true);

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          maximumAge: 60000,
          timeout: 12000
        });
      });
      const location = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        label: "your live location"
      };
      setLiveLocation(location);
      setLocationMode("live");
      return location;
    } catch {
      throw new Error("Location permission was blocked or timed out.");
    } finally {
      setIsLocating(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="search-panel" aria-label="Restaurant search">
          <div className="brand-row">
            <div className="brand-mark" aria-hidden="true">
              <Utensils size={22} />
            </div>
            <div>
              <p className="eyebrow">FoodDuel</p>
              <h1>Compare delivery choices before you order.</h1>
            </div>
          </div>

          <form className="search-form" onSubmit={handleSubmit}>
            <section className="food-picker" aria-label="Popular food choices">
              <div className="section-heading">
                <span>Cuisine</span>
                <strong>{foodChoices.length} choices</strong>
              </div>
              <div className="input-wrap cuisine-filter">
                <Search size={18} aria-hidden="true" />
                <input
                  value={cuisineSearch}
                  maxLength={40}
                  onChange={(event) => setCuisineSearch(event.target.value)}
                  placeholder="Filter cuisines"
                />
              </div>
              <div className="food-grid">
                {visibleCuisines.map((choice) => (
                  <button
                    className={form.query === choice.query ? "food-tile active" : "food-tile"}
                    disabled={isLoading}
                    key={choice.query}
                    type="button"
                    onClick={() => selectFood(choice.query)}
                  >
                    <img
                      src={cuisinePhotoUrl(choice)}
                      alt=""
                      loading="lazy"
                      onError={(event) => {
                        event.currentTarget.onerror = null;
                        event.currentTarget.src = cuisineImages[choice.category];
                      }}
                    />
                    <span>{choice.label}</span>
                  </button>
                ))}
              </div>
            </section>

            <label>
              <span>Restaurant or dish</span>
              <div className="input-wrap">
                <Search size={18} aria-hidden="true" />
                <input
                  value={form.query}
                  maxLength={100}
                  onChange={(event) => setForm({ ...form, query: event.target.value })}
                  placeholder="Search anything"
                />
              </div>
            </label>

            <div className="location-mode" aria-label="Location mode">
              <button
                className={locationMode === "pincode" ? "mode-button active" : "mode-button"}
                type="button"
                onClick={() => {
                  setLocationMode("pincode");
                  setActiveLocation(null);
                }}
              >
                <MapPin size={16} aria-hidden="true" />
                <span>PIN code</span>
              </button>
              <button
                className={locationMode === "live" ? "mode-button active" : "mode-button"}
                type="button"
                onClick={() => {
                  setLocationMode("live");
                  setActiveLocation(null);
                }}
              >
                <LocateFixed size={16} aria-hidden="true" />
                <span>Live</span>
              </button>
            </div>

            {locationMode === "pincode" ? (
              <label>
                <span>PIN code</span>
                <div className="input-wrap">
                  <MapPin size={18} aria-hidden="true" />
                  <input
                    required
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    value={form.pincode}
                    maxLength={6}
                    onChange={(event) => {
                      setForm({ ...form, pincode: event.target.value.replace(/\D/g, "") });
                      setActiveLocation(null);
                    }}
                    placeholder="500081"
                  />
                </div>
              </label>
            ) : (
              <div className="live-location-box">
                <button
                  className="secondary-button"
                  disabled={isLocating}
                  type="button"
                  onClick={() => {
                    setError("");
                    requestLiveLocation().catch((err) => {
                      setError(err instanceof Error ? err.message : "Could not fetch live location.");
                    });
                  }}
                >
                  {isLocating ? <Loader2 className="spin" size={17} /> : <LocateFixed size={17} />}
                  <span>{liveLocation ? "Refresh live location" : "Use my location"}</span>
                </button>
                <p>{liveLocation?.label ?? "Browser permission is required for live location."}</p>
              </div>
            )}

            <label>
              <span>Radius</span>
              <select
                value={form.radius}
                onChange={(event) => setForm({ ...form, radius: event.target.value })}
              >
                <option value="1000">1 km</option>
                <option value="3000">3 km</option>
                <option value="5000">5 km</option>
                <option value="10000">10 km</option>
              </select>
            </label>

            <button className="primary-button" disabled={isLoading} type="submit">
              {isLoading ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />}
              <span>{isLoading ? "Comparing" : "Compare now"}</span>
            </button>
          </form>

          {error && <p className="error-message">{error}</p>}

          <div className="status-stack" aria-label="Backend status">
            <div>
              <ShieldCheck size={18} aria-hidden="true" />
              <span>Google Places fallback ready</span>
            </div>
            <div>
              <Sparkles size={18} aria-hidden="true" />
              <span>Swiggy and Zomato adapters prepared</span>
            </div>
          </div>
        </aside>

        <section className="results-area" aria-live="polite">
          <div className="hero-strip">
            <img src={featuredImage} alt="A spread of Indian food dishes" />
            <div className="hero-copy">
              <p className="eyebrow">{locationLabel} preview</p>
              <h2>{resultSummary}</h2>
              <span>{cached ? "Served from cache" : "Live backend response"}</span>
            </div>
          </div>

          <div className="results-grid">
            {results.length > 0 ? (
              results.map((restaurant) => (
                <RestaurantCard
                  key={`${restaurant.name}-${restaurant.address}`}
                  restaurant={restaurant}
                  menu={menuByKey[restaurant.google_place_id || `${restaurant.name}-${restaurant.address || ""}`]}
                  isMenuOpen={openMenuKey === (restaurant.google_place_id || `${restaurant.name}-${restaurant.address || ""}`)}
                  isMenuLoading={menuLoadingKey === (restaurant.google_place_id || `${restaurant.name}-${restaurant.address || ""}`)}
                  menuError={menuError}
                  onToggleMenu={() => toggleRestaurantMenu(restaurant)}
                />
              ))
            ) : (
              <EmptyState isLoading={isLoading} />
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function EmptyState({ isLoading }: { isLoading: boolean }) {
  return (
    <div className="empty-state">
      {isLoading ? <Loader2 className="spin" size={26} /> : <Search size={26} />}
      <h2>{isLoading ? "Checking nearby restaurants" : "Ready for the first duel"}</h2>
      <p>
        Search results will appear here with delivery time, fee, rating, and open status
        for each platform.
      </p>
    </div>
  );
}

function formatLocationLabel(label: string) {
  return label
    .replace(/\s*,?\s*India$/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function RestaurantCard({
  restaurant,
  menu,
  isMenuOpen,
  isMenuLoading,
  menuError,
  onToggleMenu
}: {
  restaurant: UnifiedRestaurant;
  menu?: RestaurantMenuResponse;
  isMenuOpen: boolean;
  isMenuLoading: boolean;
  menuError: string;
  onToggleMenu: () => void;
}) {
  const cheaper = restaurant.cheaper_platform;
  const saving = restaurant.estimated_saving ?? 0;
  const imageUrl = apiAssetUrl(
    restaurant.swiggy?.image_url ?? restaurant.zomato?.image_url ?? fallbackRestaurantImage(restaurant.name)
  );

  return (
    <article className="restaurant-card">
      <img
        className="restaurant-image"
        src={imageUrl}
        alt=""
        loading="lazy"
        onError={(event) => {
          event.currentTarget.onerror = null;
          event.currentTarget.src = apiAssetUrl(fallbackRestaurantImage(restaurant.name));
        }}
      />
      <div className="restaurant-head">
        <div>
          <h3>{restaurant.name}</h3>
          <p>
            <MapPin size={15} aria-hidden="true" />
            <span>{restaurant.address || "Address not available"}</span>
          </p>
        </div>
        {cheaper && (
          <div className="saving-badge">
            <IndianRupee size={14} aria-hidden="true" />
            <span>{saving > 0 ? `${saving} saved on ${cheaper}` : "Same fee"}</span>
          </div>
        )}
      </div>

      <div className="platform-grid">
        <PlatformPanel label="Swiggy" listing={restaurant.swiggy} cheaper={cheaper === "swiggy"} />
        <PlatformPanel label="Zomato" listing={restaurant.zomato} cheaper={cheaper === "zomato"} />
      </div>

      <div className="menu-actions">
        <button className="secondary-button menu-toggle" type="button" onClick={onToggleMenu}>
          {isMenuLoading ? (
            <Loader2 className="spin" size={17} aria-hidden="true" />
          ) : isMenuOpen ? (
            <ChevronUp size={17} aria-hidden="true" />
          ) : (
            <ChevronDown size={17} aria-hidden="true" />
          )}
          <span>{isMenuOpen ? "Hide menu" : "View menu & prices"}</span>
        </button>
      </div>

      {isMenuOpen && (
        <MenuPanel menu={menu} isLoading={isMenuLoading} error={menuError} />
      )}
    </article>
  );
}

function MenuPanel({
  menu,
  isLoading,
  error
}: {
  menu?: RestaurantMenuResponse;
  isLoading: boolean;
  error: string;
}) {
  if (isLoading) {
    return (
      <section className="restaurant-menu">
        <Loader2 className="spin" size={22} aria-hidden="true" />
        <p>Loading menu prices...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="restaurant-menu">
        <p className="menu-note error">{error}</p>
      </section>
    );
  }

  if (!menu) {
    return null;
  }

  return (
    <section className="restaurant-menu" aria-label={`${menu.restaurant_name} menu`}>
      <div className="menu-header">
        <div>
          <h4>Menu prices</h4>
          <p>{menu.source === "estimated_preview" ? "Estimated preview" : "Live provider menu"}</p>
        </div>
        <span>{menu.items.length} items</span>
      </div>

      <div className="menu-list">
        {menu.items.map((item) => (
          <div className="menu-item" key={`${item.category}-${item.name}`}>
            <div>
              <strong>{item.name}</strong>
              <span>
                {item.category}
                {item.is_veg ? " · Veg" : " · Non-veg"}
                {item.is_popular ? " · Popular" : ""}
              </span>
            </div>
            <b>₹{Math.round(item.price)}</b>
          </div>
        ))}
      </div>

      {menu.disclaimer && <p className="menu-note">{menu.disclaimer}</p>}
    </section>
  );
}

function fallbackRestaurantImage(name: string) {
  const lowerName = name.toLowerCase();
  if (lowerName.includes("pizza")) {
    return cuisineImages.global;
  }
  if (lowerName.includes("burger")) {
    return cuisineImages.snack;
  }
  if (lowerName.includes("momo")) {
    return cuisineImages.snack;
  }
  if (lowerName.includes("dosa")) {
    return cuisineImages.indian;
  }
  if (lowerName.includes("sweet") || lowerName.includes("dessert")) {
    return cuisineImages.dessert;
  }
  return cuisineImages.indian;
}

function PlatformPanel({
  label,
  listing,
  cheaper
}: {
  label: string;
  listing?: PlatformListing | null;
  cheaper: boolean;
}) {
  if (!listing) {
    return (
      <section className="platform-panel muted">
        <div className="platform-title">
          <h4>{label}</h4>
          <span>Pending</span>
        </div>
        <p>No listing returned yet.</p>
      </section>
    );
  }

  const isOpen = listing.operating_hours?.is_open_now;
  const hasDeliveryFee = typeof listing.delivery_fee === "number";

  return (
    <section className={cheaper ? "platform-panel winner" : "platform-panel"}>
      <div className="platform-title">
        <h4>{label}</h4>
        <span>{cheaper ? "Best fee" : isOpen ? "Open" : "Closed"}</span>
      </div>

      <div className="metric-row">
        <span>
          <Clock3 size={15} aria-hidden="true" />
          {listing.delivery_time_minutes ? `${listing.delivery_time_minutes} min` : "Time soon"}
        </span>
        <span>
          <IndianRupee size={15} aria-hidden="true" />
          {hasDeliveryFee ? listing.delivery_fee : "Fee soon"}
        </span>
        <span>
          <Star size={15} aria-hidden="true" />
          {listing.rating ? listing.rating.toFixed(1) : "Rating soon"}
        </span>
      </div>

      {listing.discount_label && <p className="discount">{listing.discount_label}</p>}
    </section>
  );
}

export default App;
