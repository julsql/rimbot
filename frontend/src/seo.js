// Métadonnées SEO par route : source unique pour le HTML pré-généré (vite.config.js)
// et pour la mise à jour côté client lors de la navigation SPA (App.jsx).
export const SITE_URL = "https://rimbot.julsql.fr";

export const PAGES = {
  "/": {
    title: "Rimbot — Générateur de poèmes français aléatoires en ligne",
    description:
      "Rimbot génère des poèmes français aléatoires : choisissez le schéma de rimes (ABBA, ABAB…), le nombre de syllabes par vers et la phonétique des rimes imposées.",
  },
  "/aide": {
    title: "Aide phonétique — Syllabes et rimes disponibles | Rimbot",
    description:
      "Liste des syllabes utilisables pour imposer des rimes dans Rimbot, avec leur écriture courante, leur notation API et leur nombre d’occurrences dans la base.",
    file: "aide.html",
  },
};

export function pageUrl(path) {
  return `${SITE_URL}${path}`;
}

const escapeAttr = (s) => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;");

// Remplace le content de <meta {key}="{name}" ...>, que la balise soit sur une ou plusieurs lignes.
const setAttr = (html, key, name, value) =>
  html.replace(
    new RegExp(`(<meta\\s+${key}="${name}"\\s+content=")[^"]*(")`),
    `$1${escapeAttr(value)}$2`
  );

// Réécrit les balises propres à une page dans le HTML construit (index.html de la home).
export function renderPageHtml(html, path) {
  const page = PAGES[path];
  const url = pageUrl(path);
  let out = html.replace(/<title>[^<]*<\/title>/, `<title>${page.title}</title>`);
  out = setAttr(out, "name", "description", page.description);
  out = setAttr(out, "property", "og:title", page.title);
  out = setAttr(out, "property", "og:description", page.description);
  out = setAttr(out, "property", "og:url", url);
  out = setAttr(out, "name", "twitter:title", page.title);
  out = setAttr(out, "name", "twitter:description", page.description);
  out = out.replace(/(<link rel="canonical" href=")[^"]*(")/, `$1${url}$2`);
  return out;
}

// Applique les métadonnées de la route courante au document (navigation côté client).
export function applyPageMeta(doc, path) {
  const page = PAGES[path] || PAGES["/"];
  const url = pageUrl(PAGES[path] ? path : "/");
  doc.title = page.title;
  const set = (sel, attr, value) => doc.querySelector(sel)?.setAttribute(attr, value);
  set('meta[name="description"]', "content", page.description);
  set('meta[property="og:title"]', "content", page.title);
  set('meta[property="og:description"]', "content", page.description);
  set('meta[property="og:url"]', "content", url);
  set('meta[name="twitter:title"]', "content", page.title);
  set('meta[name="twitter:description"]', "content", page.description);
  set('link[rel="canonical"]', "href", url);
}
