// App.jsx
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./components/pages/home/home";
import Login from "./components/pages/login";

export default function App() {
  return (
    <Router>
      <main
        className="p-4 bg-slate-950 min-h-screen h-screen"
        style={{ fontFamily: 'Kanit, sans-serif', fontWeight: 900 }}
      >
        {/* Rutas */}
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/home" element={<Home />} />
        </Routes>
      </main>
    </Router>
  );
}
