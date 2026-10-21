import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { PAGES, renderPageHtml, applyPageMeta } from "../seo.js";

const html = readFileSync(resolve(__dirname, "../../index.html"), "utf8");
const doc = new DOMParser().parseFromString(html, "text/html");
const attr = (sel, a = "content") => doc.querySelector(sel)?.getAttribute(a);

describe("index.html SEO", () => {
  it("déclare la langue et les balises essentielles", () => {
    expect(doc.documentElement.getAttribute("lang")).toBe("fr");
    expect(doc.title).toBe(PAGES["/"].title);
    expect(attr('meta[name="description"]')).toBe(PAGES["/"].description);
    expect(attr('link[rel="canonical"]', "href")).toBe("https://rimbot.julsql.fr/");
    expect(attr('meta[name="theme-color"]')).toBeTruthy();
    expect(attr('link[rel="icon"]', "href")).toBe("/plume.png");
    expect(attr('link[rel="apple-touch-icon"]', "href")).toBe("/plume.png");
    expect(attr('meta[name="robots"]')).not.toMatch(/noindex/);
  });

  it("contient Open Graph et Twitter Card", () => {
    for (const p of ["og:title", "og:description", "og:url", "og:type", "og:locale"]) {
      expect(attr(`meta[property="${p}"]`)).toBeTruthy();
    }
    expect(attr('meta[property="og:image"]')).toBe("https://rimbot.julsql.fr/plume.png");
    expect(attr('meta[name="twitter:card"]')).toBe("summary");
  });

  it("contient un JSON-LD valide", () => {
    const ld = JSON.parse(doc.querySelector('script[type="application/ld+json"]').textContent);
    const types = ld["@graph"].map((n) => n["@type"]);
    expect(types).toEqual(expect.arrayContaining(["WebSite", "WebApplication", "Person"]));
  });

  it.each(Object.entries(PAGES))("respecte les longueurs pour %s", (_, page) => {
    expect(page.title.length).toBeGreaterThanOrEqual(50);
    expect(page.title.length).toBeLessThanOrEqual(60);
    expect(page.description.length).toBeGreaterThanOrEqual(140);
    expect(page.description.length).toBeLessThanOrEqual(160);
  });
});

describe("renderPageHtml", () => {
  it("réécrit les métadonnées de /aide sans toucher au JSON-LD", () => {
    const out = new DOMParser().parseFromString(renderPageHtml(html, "/aide"), "text/html");
    const get = (sel, a = "content") => out.querySelector(sel).getAttribute(a);
    expect(out.title).toBe(PAGES["/aide"].title);
    expect(get('meta[name="description"]')).toBe(PAGES["/aide"].description);
    expect(get('meta[property="og:url"]')).toBe("https://rimbot.julsql.fr/aide");
    expect(get('meta[name="twitter:title"]')).toBe(PAGES["/aide"].title);
    expect(get('link[rel="canonical"]', "href")).toBe("https://rimbot.julsql.fr/aide");
    expect(out.querySelector('script[type="application/ld+json"]').textContent).toContain(
      '"url": "https://rimbot.julsql.fr/"'
    );
  });
});

describe("applyPageMeta", () => {
  it("retombe sur la home pour une route inconnue", () => {
    const d = new DOMParser().parseFromString(html, "text/html");
    applyPageMeta(d, "/inconnue");
    expect(d.title).toBe(PAGES["/"].title);
  });
});
