"use strict";
(function () {
  const ENDPOINTS = {
    divar: "https://divar-mcp.mmdju2.workers.dev/mcp",
    digikala: "https://digikala-mcp.mmdju.workers.dev/mcp",
  };
  let rpcId = 0;

  function parsePayload(text) {
    const dataLines = text
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trim())
      .filter(Boolean);
    const envelope = JSON.parse(dataLines.length ? dataLines.at(-1) : text);
    if (envelope.error)
      throw new Error(envelope.error.message || JSON.stringify(envelope.error));
    const result = envelope.result;
    if (Array.isArray(result?.content)) {
      for (const part of result.content) {
        if (part?.type === "text" && typeof part.text === "string") {
          try {
            return JSON.parse(part.text);
          } catch {
            return { message: part.text };
          }
        }
      }
    }
    return result;
  }

  async function call(source, name, args = {}, timeoutMs = 26000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(ENDPOINTS[source], {
        method: "POST",
        headers: {
          "content-type": "application/json",
          accept: "application/json, text/event-stream",
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: ++rpcId,
          method: "tools/call",
          params: { name, arguments: args },
        }),
        signal: controller.signal,
      });
      if (!response.ok)
        throw new Error(`پاسخ ${response.status} از منبع ${source}`);
      return parsePayload(await response.text());
    } finally {
      clearTimeout(timer);
    }
  }

  function normalizeOffer(raw, source) {
    return {
      id: String(raw.token ?? raw.id ?? ""),
      title: raw.title || raw.name || "بدون عنوان",
      price: Number.isFinite(Number(raw.price_toman))
        ? Number(raw.price_toman)
        : null,
      url: raw.url || null,
      image: raw.thumbnail || raw.image || null,
      city: raw.city || null,
      district: raw.district || null,
      seller: raw.seller || null,
      rating: Number.isFinite(Number(raw.rating_stars))
        ? Number(raw.rating_stars)
        : null,
      ratingCount: Number.isFinite(Number(raw.rating_count))
        ? Number(raw.rating_count)
        : null,
      placeholder: Boolean(raw.price_is_placeholder),
      placeholderNote: raw.price_note || null,
      negotiable: Boolean(raw.negotiable),
      hasChat: raw.has_chat ?? null,
      timeAgo: raw.time_ago || null,
      badges: Array.isArray(raw.badges) ? raw.badges : [],
      source,
      raw,
    };
  }

  async function searchProperties({
    city = "نوشهر",
    limit = 20,
    pages = 2,
  } = {}) {
    const result = await call("divar", "search_ads", {
      query: "مغازه",
      category: "shop-rent",
      city,
      pages,
      limit,
    });
    return {
      items: (result.items || []).map((item) => normalizeOffer(item, "divar")),
      candidates: result.candidates ?? null,
      collectedAt: new Date().toISOString(),
      attribution: result.attribution || null,
    };
  }

  async function getPropertyDetails(token) {
    if (!token) throw new Error("توکن آگهی ملک موجود نیست");
    return call("divar", "ad_details", { token, detail: "full" }, 32000);
  }

  async function searchEquipment(item, budget) {
    const safeBudget = Math.max(1000000, Math.round(Number(budget) || 0));
    const usedPromise = call("divar", "find_best_value", {
      query: item.used_query,
      category: "cafe-and-restaurant",
      cities: ["نوشهر", "ساری", "آمل", "بابل", "رشت"],
      budget_toman: safeBudget,
      include_negotiable: false,
      limit: 3,
    });
    const newPromise = call("digikala", "find_best_value", {
      query: item.new_query,
      budget_toman: safeBudget,
      pages: 1,
      limit: 3,
    });
    const [used, newItems] = await Promise.allSettled([
      usedPromise,
      newPromise,
    ]);
    const usedValue = used.status === "fulfilled" ? used.value : null;
    const newValue = newItems.status === "fulfilled" ? newItems.value : null;
    return {
      used: {
        items: (usedValue?.picks || usedValue?.items || []).map((x) =>
          normalizeOffer(x, "divar"),
        ),
        marketMedian: usedValue?.market_scale?.median_toman ?? null,
        error: used.status === "rejected" ? String(used.reason) : null,
      },
      new: {
        items: (newValue?.picks || newValue?.items || []).map((x) =>
          normalizeOffer(x, "digikala"),
        ),
        seller: newValue?.top_pick_seller || null,
        warranty: newValue?.top_pick_warranty || null,
        error: newItems.status === "rejected" ? String(newItems.reason) : null,
      },
      collectedAt: new Date().toISOString(),
    };
  }

  window.RestaurantMarket = {
    call,
    searchProperties,
    getPropertyDetails,
    searchEquipment,
    endpoints: { ...ENDPOINTS },
  };
})();
