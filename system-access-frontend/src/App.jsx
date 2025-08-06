import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import LiveFeed from './pages/LiveFeed';
import Employees from './pages/Employees';
import AccessLogs from './pages/AccessLogs';
import CameraHealth from './pages/CameraHealth';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <NavBar />
        <main className="pt-16">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/live-feed" element={<LiveFeed />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/logs" element={<AccessLogs />} />
            <Route path="/cameras" element={<CameraHealth />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
