
// src/App.jsx

import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";

import Home from "./pages/Home";
import MonitoringDashboard from "./components/MonitoringDashboard";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Main homepage */}
                <Route path="/" element={<Home />} />

                {/* Internal system monitor */}
                <Route 
			path="/monitor"
  			element={
    				<ProtectedRoute>
      					<MonitoringDashboard />
    				</ProtectedRoute>
  		        } 
	        />
            </Routes>
        </BrowserRouter>
    );
}

export default App;