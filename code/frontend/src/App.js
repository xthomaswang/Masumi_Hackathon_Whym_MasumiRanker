import React from 'react';
// 确保从正确的路径导入 AgentsProvider
import { AgentsProvider } from './context'; // 假设 context.jsx 在 src 目录下
import Sidebar from './component/sidebar';
import Home from './pages/home';
import Detail from './pages/detail';
import Categories from './pages/categories';
import Contact from './pages/contact';
import Category from './pages/category';
import Test from './pages/test';
import { Routes, Route, BrowserRouter } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      {/* 将 AgentsProvider 放在这里，包裹住 Routes */}
      {/* 这样，所有路由及其子组件都可以通过 useAgentsContext 访问状态 */}
      <AgentsProvider>
        <Routes>
          {/* Sidebar 作为布局组件，包含 Outlet 来渲染子路由 */}
          <Route path='/' element={<Sidebar />}>
            {/* 子路由 */}
            <Route index element={<Home />} />
            <Route path='categories' element={<Categories />} />
            <Route path='detail/:id' element={<Detail />} />
            <Route path='contact' element={<Contact />} />
            <Route path='category/:tag' element={<Category />} />            
            <Route path='test' element={<Test />} />
          </Route>
        </Routes>
      </AgentsProvider>
    </BrowserRouter>
  );
}

export default App;