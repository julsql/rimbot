import { Link, NavLink, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage.jsx";
import HelpPage from "./pages/HelpPage.jsx";

export default function App() {
  return (
    <div className="layout">
      <header className="topbar">
        <Link to="/" className="brand">Poème</Link>
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
        <span>Poème — projet scolaire de génération de poèmes français.</span>
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
