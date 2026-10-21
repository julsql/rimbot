import { useEffect } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import HomePage from "./pages/HomePage.jsx";
import HelpPage from "./pages/HelpPage.jsx";
import { applyPageMeta } from "./seo.js";

function usePageMeta() {
  const { pathname } = useLocation();
  useEffect(() => {
    applyPageMeta(document, pathname.replace(/\/+$/, "") || "/");
  }, [pathname]);
}

export default function App() {
  usePageMeta();
  return (
    <div className="layout">
      <header className="topbar">
        <Link to="/" className="brand">Rimbot</Link>
        <nav>
          <NavLink to="/" end>Générateur</NavLink>
          <NavLink to="/aide">Aide phonétique</NavLink>
        </nav>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/aide" element={<HelpPage />} />
        </Routes>
      </main>

      <footer className="footer">
        <span>Rimbot — projet scolaire de génération de poèmes français.</span>
        <span className="footer-author">
          {" · "}
          <a
            href="https://github.com/julsql"
            target="_blank"
            rel="noreferrer noopener"
          >
            @julsql
          </a>
        </span>
      </footer>
    </div>
  );
}
