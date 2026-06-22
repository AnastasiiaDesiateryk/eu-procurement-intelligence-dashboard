import React from "react";

import { NavLink } from "react-router-dom";

export default function Nav() {
  return (
    <nav className="nav">
      <div className="brand">SCM MVP</div>
      <div className="links">
        <NavLink to="/overview">Overview</NavLink>
        <NavLink to="/suppliers">Suppliers</NavLink>
        <NavLink to="/finance">Finance (C2C)</NavLink>
      </div>
    </nav>
  );
}
