import React from 'react';
import Sidebar from './component/sidebar';
import Agents from './component/agents';
import Footer from './component/footer';
import Home from './pages/home';
import Detail from './pages/detail';
import Ranking from './pages/ranking';
import Contact from './pages/contact';
import {Routes, Route, BrowserRouter} from 'react-router-dom';

import './App.css';

function App() {
  return (
    <BrowserRouter>
  <Routes>
    <Route path='/' element={<Sidebar />}>
      <Route index element={<Home />} />
      <Route path='ranking' element={<Ranking />} />
      <Route path='detail' element={<Detail />} />
      <Route path='contact' element={<Contact />} />
     
    </Route>
  </Routes>
</BrowserRouter>

  );
}

export default App;
