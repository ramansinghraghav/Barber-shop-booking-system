import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import CustomerDashboard from "./pages/CustomerDashboard";
import BarberDashboard from "./pages/BarberDashboard";

function App() {
  const token = localStorage.getItem("access_token");
  const user = JSON.parse(localStorage.getItem("user") || "null");

  return (
    <BrowserRouter>
      <Routes>

        {/* Default route */}
        <Route
          path="/"
          element={
            token
              ? user?.role === "customer"
                ? <Navigate to="/customer" />
                : <Navigate to="/barber" />
              : <Navigate to="/login" />
          }
        />

        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route path="/customer" element={<CustomerDashboard />} />
        <Route path="/barber" element={<BarberDashboard />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;