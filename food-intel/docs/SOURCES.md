# Source registry — v0.2

The source registry is intentionally curated rather than exhaustive. A source is activated only when it adds meaningful coverage and a stable machine-readable feed has been confirmed.

## Current footprint

- 28 registered sources
- 18 active RSS feeds
- 10 discovery / verification targets
- Coverage spans restaurant/QSR, fast casual, restaurant operations, food tech, equipment, food manufacturing, food safety, cold chain and regulation.

## Priority tiers

### Priority 1 — core signal sources

High-value sources that should materially influence the daily intelligence layer. These include major restaurant/food industry publications, specialist technology/equipment outlets and official regulators.

Examples: Restaurant Dive, Food Dive, Fast Casual, QSRweb, Restaurant Business, The Spoon, Food Safety News, Food Engineering, Foodservice Equipment Reports and FDA safety feeds.

### Priority 2 — specialist depth

Sources that deepen a particular operating or technical domain such as management, restaurant technology, cold chain or equipment.

### Priority 3 — niche / supplemental

Useful vertical sources that broaden coverage without being allowed to dominate the overall feed.

## Activation rule

A source can be `enabled: true` only when:

1. It exposes a stable HTTPS RSS/Atom endpoint.
2. The endpoint has been independently checked.
3. The source has a clear industry role and is not merely duplicating a stronger source.
4. The source has default category metadata.
5. A `verified_at` date is recorded.

Sources that are strategically useful but do not yet pass those checks remain `type: discovery` and `enabled: false`.

## Coverage map

### Restaurant / QSR / fast casual

- Restaurant Dive
- Fast Casual
- QSRweb
- Restaurant Business
- Modern Restaurant Management
- RestaurantNews.com
- Pizza Marketplace

### Restaurant technology / food tech

- The Spoon
- Restaurant Technology News

### Food safety / regulatory

- Food Safety News
- FDA Food Safety Recalls
- FDA Outbreaks

### Manufacturing / processing / cold chain

- Food Dive
- Food Engineering
- Food Business News — Food Manufacturers
- Refrigerated & Frozen Foods

### Foodservice equipment

- Foodservice Equipment Reports
- Foodservice Equipment Journal

## Discovery queue

The registry also tracks strategically important sources that are not yet active, including QSR Magazine, Nation's Restaurant News, Prepared Foods, Food Safety Magazine, MEAT+POULTRY, Dairy Foods, USDA FSIS, New Food Magazine, FoodNavigator-USA and Food Truck Operator.

This queue exists so source research is preserved without allowing an uncertain feed to degrade the automated collector.

## Next source work

The next expansion pass should focus on three gaps:

1. Iran and Persian-language food/restaurant industry sources.
2. International restaurant/foodservice coverage outside North America.
3. First-party company feeds for major restaurant groups and suppliers, kept separate from editorial sources so corporate announcements can be weighted differently.
