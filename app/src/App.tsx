import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Nav from "./components/Nav";
import Overview from "./pages/Overview";
import Suppliers from "./pages/Suppliers";
import Finance from "./pages/Finance";

export default function App() {
  return (
    <div className="app">
      <Nav />
      <div className="container">
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/suppliers" element={<Suppliers />} />
          <Route path="/finance" element={<Finance />} />
        </Routes>
      </div>
    </div>
  );
}
