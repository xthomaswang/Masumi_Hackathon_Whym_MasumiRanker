// src/pages/contact.jsx
import React from 'react';

const Contact = () => {
  return (
    <div className="contact-page">
      <div className="contact-card">
        <h1 className="contact-title">Contact Us</h1>
        <p className="contact-subtext">
          Got questions? Interested in building with us?  
          <br />We’d love to hear from you.
        </p>

        <div className="contact-info">
          <p><strong>Email:</strong> contact@whym.ai</p>
          <p><strong>Phone:</strong> +1 (123) 456-7890</p>
          <p><strong>Location:</strong> San Francisco, CA</p>
        </div>

        <div className="contact-signature">
          — The W.H.Y.M Team 🌈
        </div>
      </div>
    </div>
  );
};

export default Contact;
