import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/Layout/AppLayout';
import RequirementImport from './pages/RequirementImport';
import SignalMatrix from './pages/SignalMatrix';
import TestCaseGen from './pages/TestCaseGen';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<RequirementImport />} />
            <Route path="requirements" element={<RequirementImport />} />
            <Route path="signals" element={<SignalMatrix />} />
            <Route path="testcases" element={<TestCaseGen />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
