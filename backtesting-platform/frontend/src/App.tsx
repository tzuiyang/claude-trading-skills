import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import UniversePage from "./pages/UniversePage";
import StockDetailPage from "./pages/StockDetailPage";
import ComparisonPage from "./pages/ComparisonPage";

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const active = useLocation().pathname === to;
  return (
    <Link to={to} className={`nav-link ${active ? "active" : ""}`}>
      {children}
    </Link>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-root">
        <nav className="top-nav">
          <span className="brand">Backtesting Platform</span>
          <NavLink to="/">Universe</NavLink>
          <NavLink to="/compare">Compare</NavLink>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<UniversePage />} />
            <Route path="/stock/:ticker" element={<StockDetailPage />} />
            <Route path="/compare" element={<ComparisonPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
