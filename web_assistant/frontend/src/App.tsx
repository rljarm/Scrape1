import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import styled from 'styled-components';
import CrawlConfig from './components/CrawlConfig';
import Dashboard from './components/Dashboard';

// CRITICAL: Main application routing and layout
// TODO(future): Add authentication guards
// CHECK(periodic): Verify route accessibility

const AppContainer = styled.div`
  min-height: 100vh;
  background-color: #f8f9fa;
`;

const NavBar = styled.nav`
  background-color: #343a40;
  padding: 1rem;
  color: white;
`;

const NavList = styled.ul`
  display: flex;
  gap: 2rem;
  list-style: none;
  margin: 0;
  padding: 0;
`;

const NavLink = styled(Link)`
  color: white;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    color: #007bff;
  }
`;

const MainContent = styled.main`
  padding: 2rem;
`;

const App: React.FC = () => {
  return (
    <Router>
      <AppContainer>
        <NavBar>
          <NavList>
            <li>
              <NavLink to="/">Dashboard</NavLink>
            </li>
            <li>
              <NavLink to="/config">Create Configuration</NavLink>
            </li>
          </NavList>
        </NavBar>

        <MainContent>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/config" element={<CrawlConfig />} />
          </Routes>
        </MainContent>
      </AppContainer>
    </Router>
  );
};

export default App;
