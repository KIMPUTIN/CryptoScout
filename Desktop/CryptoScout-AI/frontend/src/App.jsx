
// src/App.jsx

import { BrowserRouter, Routes, Route } from "react-router-dom";

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
    				user?.email === "webappsforfun@gmail.com"
      				  ? <MonitoringDashboard />
      				  : <div>Unauthorized</div>
  		        } 
	        />
            </Routes>
        </BrowserRouter>
    );
}

export default App;