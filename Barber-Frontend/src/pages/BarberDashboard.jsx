import { useNavigate } from "react-router-dom";
import { useState,useEffect} from "react";
import "./BarberDashboard.css";
import API from "../api/axios";

function BarberDashboard() {
  const [shopName, setShopName] = useState("");
  const [address, setAddress] = useState("");
  const [openTime, setOpenTime] = useState("");
  const [closeTime, setCloseTime] = useState("");

  const [serviceName, setServiceName] = useState("");
  const [price, setPrice] = useState("");
  const [duration, setDuration] = useState("");
  const [shopId, setShopId] = useState(null);
  useEffect(() => {
  API.get("/my-shop")
    .then((res) => {
      setShopId(res.data.shop_id);
    })
    .catch(() => {
      alert("Shop not found");
    });
}, []);

  const [serviceId, setServiceId] = useState("");

  // Create Shop
  const createShop = async () => {
    try {
      const res = await API.post("/shops", {
        shop_name: shopName,
        address,
        open_time: openTime,
        close_time: closeTime,
      });

      alert("Shop Created ✅");
    } catch (err) {
      alert("Shop creation failed ❌");
      console.log(err);
    }
  };

  // Add Service
  const addService = async () => {
    try {
      await API.post("/service", {
        shop_id: shopId,
        name: serviceName,
        price,
        duration,
      });

      alert("Service Added ✅");
    } catch (err) {
      alert("Service failed ❌");
      console.log(err);
    }
  };

  // Generate Slots
  const generateSlots = async () => {
    try {
      await API.post("/generate-slots", {
        service_id: serviceId,
      });

      alert("Slots Generated ✅");
    } catch (err) {
      alert("Slot generation failed ❌");
      console.log(err);
    }
  };

  const navigate = useNavigate();

  const handleLogout = () => {
   localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  navigate("/login");
};

  return (
  <div className="dashboard">

    {/* TOP BAR */}
    <div className="topbar">
      <h2>Barber Dashboard</h2>
      <button onClick={handleLogout}>Logout</button>
    </div>

    {/* ADD SERVICE */}
    <div className="section">
      <h3>Add Service</h3>

      <div className="form-row">

        <input placeholder="Service Name"
          onChange={(e) => setServiceName(e.target.value)} />

        <input placeholder="Price"
          onChange={(e) => setPrice(e.target.value)} />

        <input placeholder="Duration (minutes)"
          onChange={(e) => setDuration(e.target.value)} />

        <button onClick={addService}>Add Service</button>
      </div>
    </div>

    {/* GENERATE SLOTS */}
    <div className="section">
      <h3>Generate Slots</h3>

      <div className="form-row">
        <input placeholder="Service ID"
          onChange={(e) => setServiceId(e.target.value)} />

        <button onClick={generateSlots}>Generate Slots</button>
      </div>
    </div>

  </div>
  );
}

export default BarberDashboard;