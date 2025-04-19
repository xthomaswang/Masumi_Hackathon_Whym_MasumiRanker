import React from 'react';
import Sidebar from './component/sidebar';
import Home from './pages/home';
import Detail from './pages/detail';
import Categories from './pages/categories';
import Contact from './pages/contact';
import Category from './pages/category';
import {Routes, Route, BrowserRouter} from 'react-router-dom';

import './App.css';

function App() {
  return (
    <BrowserRouter>
  <Routes>
    <Route path='/' element={<Sidebar />}>
      <Route index element={<Home />} />
      <Route path='categories' element={<Categories />} />
      <Route path='detail/:id' element={<Detail />} />
      <Route path='contact' element={<Contact />} />
      <Route path='category' element={<Category />} />
     
    </Route>
  </Routes>
</BrowserRouter>

  );
}

export default App;
