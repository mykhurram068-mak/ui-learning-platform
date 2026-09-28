/**
* currency.js — Shared currency & rate utilities for MAK Studio tools
* ------------------------------------------------------------------
* Loaded by every tool page via: <script src="/currency.js"></script>
*
* Provides a global `Currency` object with:
*   - Currency.detect()         → auto-detect user's currency from locale
*   - Currency.get()            → returns current currency code
*   - Currency.set(code)        → manually override currency
*   - Currency.symbol()         → returns symbol (Rs., $, £, etc.)
*   - Currency.format(amount)   → "Rs. 1,234,567"
*   - Currency.convert(amount, from, to) → convert between currencies
*   - Currency.rate(from, to)   → get exchange rate
*   - Currency.injectDropdown(selector) → insert currency picker into a page
*   - Currency.metalRates()     → get cached gold/silver rates per gram
*   - Currency.onChange(cb)     → callback when currency changes
*
* Rates are cached in localStorage for 24 hours to avoid rate limits.
*/

(function () {
  'use strict';

  // ============ CONFIG ============
  const CURRENCY_CACHE_KEY = 'maku_currency';
  const RATE_CACHE_KEY = 'maku_exchange_rates';
  const METAL_CACHE_KEY = 'maku_metal_rates';
  const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

  // Region → currency mapping (extend as needed)
  const REGION_TO_CURRENCY = {
    PK: 'PKR', US: 'USD', GB: 'GBP', AE: 'AED',
    SA: 'SAR', IN: 'INR', CA: 'CAD', AU: 'AUD',
    DE: 'EUR', FR: 'EUR', IT: 'EUR', ES: 'EUR',
    NL: 'EUR', IE: 'EUR', PT: 'EUR',
    MY: 'MYR', SG: 'SGD', BD: 'BDT', LK: 'LKR',
    ZA: 'ZAR', NG: 'NGN', KE: 'KES', TR: 'TRY',
    CN: 'CNY', JP: 'JPY', KR: 'KRW', ID: 'IDR',
    PH: 'PHP', TH: 'THB', VN: 'VND', NZ: 'NZD',
    CH: 'CHF', SE: 'SEK', NO: 'NOK', DK: 'DKK',
  };

  // Supported currencies for manual override (keep focused — don't list all 180)
  const SUPPORTED = [
    { code: 'PKR', name: 'Pakistani Rupee' },
    { code: 'USD', name: 'US Dollar' },
    { code: 'GBP', name: 'British Pound' },
    { code: 'EUR', name: 'Euro' },
    { code: 'AED', name: 'UAE Dirham' },
    { code: 'SAR', name: 'Saudi Riyal' },
    { code: 'INR', name: 'Indian Rupee' },
    { code: 'CAD', name: 'Canadian Dollar' },
    { code: 'AUD', name: 'Australian Dollar' },
    { code: 'MYR', name: 'Malaysian Ringgit' },
  ];

  // Fallback rates (used if API fails and no cache)
  // Base: 1 USD = X currency
  const FALLBACK_RATES_USD = {
    USD: 1, PKR: 278, GBP: 0.79, EUR: 0.92, AED: 3.67,
    SAR: 3.75, INR: 84, CAD: 1.37, AUD: 1.52, MYR: 4.4,
    JPY: 152, CNY: 7.2, TRY: 34, BDT: 120, LKR: 295,
    ZAR: 18.5, NGN: 1600, KES: 130,
  };

  // ============ STATE ============
  let currentCurrency = null;
  const changeCallbacks = [];

  // ============ DETECTION ============
  function detect() {
    const locale = navigator.language || (navigator.languages && navigator.languages[0]) || 'en-US';
    let region = 'US';
    if (locale.includes('-')) {
      region = locale.split('-')[1].toUpperCase();
    }
    return {
      code: REGION_TO_CURRENCY[region] || 'USD',
      region: region,
      locale: locale,
    };
  }

  function getStoredCurrency() {
    try {
      const stored = JSON.parse(localStorage.getItem(CURRENCY_CACHE_KEY));
      if (stored && stored.code) return stored.code;
    } catch (e) {}
    return null;
  }

  function storeCurrency(code) {
    try {
      localStorage.setItem(CURRENCY_CACHE_KEY, JSON.stringify({ code, at: Date.now() }));
    } catch (e) {}
  }

  function get() {
    if (!currentCurrency) {
      currentCurrency = getStoredCurrency() || detect().code;
    }
    return currentCurrency;
  }

  function set(code) {
    const upper = (code || '').toUpperCase();
    if (!upper) return;
    currentCurrency = upper;
    storeCurrency(upper);
    // Update any injected dropdowns
    document.querySelectorAll('[data-maku-currency-dropdown]').forEach(sel => {
      if (sel.value !== upper) sel.value = upper;
    });
    changeCallbacks.forEach(cb => { try { cb(upper); } catch (e) {} });
  }

  function onChange(cb) {
    if (typeof cb === 'function') changeCallbacks.push(cb);
  }

  // ============ FORMATTING ============
  function symbol() {
    const code = get();
    try {
      const parts = new Intl.NumberFormat(navigator.language, {
        style: 'currency',
        currency: code,
        currencyDisplay: 'narrowSymbol',
      }).formatToParts(0);
      const sym = parts.find(p => p.type === 'currency');
      return sym ? sym.value : code;
    } catch (e) {
      return code;
    }
  }

  function format(amount, opts) {
    const code = get();
    const options = Object.assign({
      style: 'currency',
      currency: code,
      maximumFractionDigits: 0,
    }, opts || {});
    try {
      return new Intl.NumberFormat(navigator.language, options).format(amount);
    } catch (e) {
      return code + ' ' + Math.round(amount).toLocaleString();
    }
  }

  // ============ EXCHANGE RATES ============
  function getCachedRates() {
    try {
      const raw = JSON.parse(localStorage.getItem(RATE_CACHE_KEY));
      if (raw && raw.rates && (Date.now() - raw.at) < CACHE_DURATION) {
        return raw.rates;
      }
    } catch (e) {}
    return null;
  }

  function cacheRates(rates) {
    try {
      localStorage.setItem(RATE_CACHE_KEY, JSON.stringify({ rates, at: Date.now() }));
    } catch (e) {}
  }

  async function fetchRates(base) {
    // Uses jsDelivr currency API (200+ currencies, no key, daily update)
    const b = (base || 'usd').toLowerCase();
    const url = `https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/${b}.json`;
    const r = await fetch(url);
    if (!r.ok) throw new Error('Rate fetch failed: ' + r.status);
    const data = await r.json();
    const raw = data[b]; // e.g., data.usd = { pkr: 278, ... }
    // Uppercase all keys for consistency
    const upper = {};
    Object.keys(raw).forEach(k => { upper[k.toUpperCase()] = raw[k]; });
    return upper;
  }

  async function getRates(base) {
    const b = (base || 'USD').toUpperCase();
    const cached = getCachedRates();
    if (cached && cached[b]) return cached[b];
    try {
      const rates = await fetchRates(b);
      // Store under base
      const store = cached || {};
      store[b] = rates;
      cacheRates(store);
      return rates;
    } catch (e) {
      console.warn('[currency.js] Using fallback rates:', e.message);
      // Build fallback rate map relative to base
      const fallback = {};
      const baseToUsd = 1 / (FALLBACK_RATES_USD[b] || 1);
      Object.keys(FALLBACK_RATES_USD).forEach(code => {
        fallback[code] = baseToUsd * FALLBACK_RATES_USD[code];
      });
      return fallback;
    }
  }

  async function rate(from, to) {
    const f = (from || 'USD').toUpperCase();
    const t = (to || 'USD').toUpperCase();
    if (f === t) return 1;
    const rates = await getRates(f);
    return rates[t] || 1;
  }

  async function convert(amount, from, to) {
    const r = await rate(from, to);
    return amount * r;
  }

  // ============ METAL RATES ============
  function getCachedMetals() {
    try {
      const raw = JSON.parse(localStorage.getItem(METAL_CACHE_KEY));
      if (raw && (Date.now() - raw.at) < CACHE_DURATION) return raw;
    } catch (e) {}
    return null;
  }

  function cacheMetals(data) {
    try {
      localStorage.setItem(METAL_CACHE_KEY, JSON.stringify(Object.assign({ at: Date.now() }, data)));
    } catch (e) {}
  }

  async function metalRates() {
    // Returns { goldPerGram, silverPerGram, currency, updated, isFallback }
    const cached = getCachedMetals();
    if (cached) return cached;

    const code = get();
    try {
      // Fetch spot price in USD per troy ounce from a public source
      // (Swaps easily if the API changes; this is a placeholder that works when available)
      const res = await fetch('https://api.gold-api.com/price/XAU');
      const gold = await res.json();
      const res2 = await fetch('https://api.gold-api.com/price/XAG');
      const silver = await res2.json();

      // 1 troy ounce = 31.1035 grams
      const USD_PER_GRAM_GOLD = gold.price / 31.1035;
      const USD_PER_GRAM_SILVER = silver.price / 31.1035;

      const usdToLocal = await rate('USD', code);

      const result = {
        goldPerGram: USD_PER_GRAM_GOLD * usdToLocal,
        silverPerGram: USD_PER_GRAM_SILVER * usdToLocal,
        currency: code,
        updated: new Date().toISOString(),
        isFallback: false,
      };
      cacheMetals(result);
      return result;
    } catch (e) {
      console.warn('[currency.js] Metal rate fetch failed, using fallback:', e.message);
      // Fallback — reasonable defaults for PKR
      const usdToLocal = await rate('USD', code);
      const fallback = {
        goldPerGram: (2400 / 31.1035 * 31.1035) * 1, // ~USD $2400/oz → placeholder
        silverPerGram: (28 / 31.1035 * 31.1035) * 1,
        currency: code,
        updated: new Date().toISOString(),
        isFallback: true,
      };
      return fallback;
    }
  }

  // ============ DROPDOWN INJECTION ============
  function injectDropdown(selector) {
    const el = typeof selector === 'string'
      ? document.querySelector(selector)
      : selector;
    if (!el) return;

    const current = get();
    const options = SUPPORTED.map(c =>
      `<option value="${c.code}"${c.code === current ? ' selected' : ''}>${c.code} — ${c.name}</option>`
    ).join('');

    el.innerHTML = `
      <label style="display:block; font-size:0.8rem; color:#94a3b8; margin-bottom:0.35rem;">Currency</label>
      <select data-maku-currency-dropdown
              style="width:100%; background:#0f172a; border:2px solid #334155; border-radius:0.5rem; padding:0.5rem; color:white; font-size:0.9rem;">
        ${options}
      </select>
    `;

    const sel = el.querySelector('select');
    sel.addEventListener('change', () => set(sel.value));
  }

  // ============ PUBLIC API ============
  window.Currency = {
    detect,
    get,
    set,
    symbol,
    format,
    rate,
    convert,
    getRates,
    metalRates,
    injectDropdown,
    onChange,
    SUPPORTED,
  };

  console.log('[currency.js] Loaded. Detected currency:', get());
})();
