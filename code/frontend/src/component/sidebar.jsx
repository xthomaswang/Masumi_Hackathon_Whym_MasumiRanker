// src/component/sidebar.jsx
import React, { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  const toggleSidebar = () => {
    document.body.classList.toggle('sb-sidenav-toggled');
    setSidebarOpen(!sidebarOpen);
  };

  const navItems = [
    { to: '/', icon: 'fa-home', label: 'Home' },
    { to: '/categories', icon: 'fa-star', label: 'Categories' },
    { to: '/contact', icon: 'fa-envelope', label: 'Contact Us' },
  ];

  return (
    <div className="sb-nav-fixed">
      {/* Top Nav */}
      <nav className="sb-topnav navbar navbar-expand navbar-dark bg-dark">
        <Link className="navbar-brand ps-3" to="/">W.H.Y.M</Link>
        <button
          className="btn btn-link btn-sm order-1 order-lg-0 me-4 me-lg-0"
          onClick={toggleSidebar}
        >
          <i className="fas fa-bars"></i>
        </button>

        <form className="d-none d-md-inline-block form-inline ms-auto me-0 me-md-3 my-2 my-md-0">
          <div className="input-group input-group-sm">
            <input
              className="form-control"
              type="text"
              placeholder="Search..."
              aria-label="Search"
              aria-describedby="btnNavbarSearch"
            />
            <button className="btn btn-primary" id="btnNavbarSearch" type="button">
              <i className="fas fa-search"></i>
            </button>
          </div>
        </form>
      </nav>

      {/* Sidenav + Content */}
      <div id="layoutSidenav">
        <div id="layoutSidenav_nav">
          <nav className="sb-sidenav accordion sb-sidenav-dark" id="sidenavAccordion">
            <div className="sb-sidenav-menu">
              <div className="nav flex-column">
                <br />
                {navItems.map((item) => (
                  <Link
                    key={item.to}
                    className={`nav-link ${location.pathname === item.to ? 'active' : ''}`}
                    to={item.to}
                  >
                    <div className="sb-nav-link-icon">
                      <i className={`fas ${item.icon}`}></i>
                    </div>
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
            <div style={{ marginLeft: '20px' }} className="sb-sidenav-footer">
              <div className="small" style={{marginTop:"3rem"}}>Hackathon Team</div><div className="small">              W.H.Y.M
              </div>
            </div>
          </nav>
        </div>

        <div id="layoutSidenav_content">
          <main className="container-fluid px-4 py-3">
            <Outlet />
          </main>
        </div>
      </div>

      {/* ✅ Footer moved outside */}
      <footer className="site-footer bg-light">
        <div className="container-fluid px-4">
          <div className="d-flex align-items-center justify-content-between small">
            <div className="text-muted">© WHYM Team 2025</div>
            <div>
              <a href="#">Privacy Policy</a>
              &middot;
              <a href="#">Terms & Conditions</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Sidebar;
