import Navbar from "../components/Navbar";
import { useEffect, useState } from "react";
import API from "../api/axios";
import { useNavigate } from "react-router-dom";

function CustomerDashboard() {
  const navigate = useNavigate();
  const [shops, setShops] = useState([]);
  const [services, setServices] = useState([]);
  const [slots, setSlots] = useState([]);

  const [selectedShop, setSelectedShop] = useState(null);
  const [selectedService, setSelectedService] = useState(null);

  // 🔹 Load all shops
  useEffect(() => {
    API.get("/api/shops")
      .then((res) => setShops(res.data.shops))
      .catch((err) => {
        console.log(err);
        alert("Failed to load shops");
      });
  }, []);

  const goBack = () => {
    setSelectedShop(null);
    setServices([]);
    setSlots([]);
  };

  const handleLogout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  navigate("/login");
  };
  const loadServices = async (shopId) => {
    try {
      const res = await API.get(`/api/shop-services/${shopId}`);
      setServices(res.data.services);
      setSelectedShop(shopId);
      setSlots([]);
    } catch (err) {
      alert("No services found");
    }
  };

  const loadSlots = async (serviceId) => {
    try {
      const res = await API.get(`/api/slots/${serviceId}`);
      setSlots(res.data.slots);
      setSelectedService(serviceId);
    } catch (err) {
      alert("No available slots");
      setSlots([]);
    }
  };

  const bookSlot = async (slotId) => {
    try {
      await API.post("/api/book-slot", {
        slot_id: slotId,
      });

      alert("Slot booked successfully 🎉");
      loadSlots(selectedService);
    } catch (err) {
      alert("Slot already booked ❌");
    }
  };

return (
  <>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <h2>Customer Dashboard</h2>
      <button onClick={handleLogout}>Logout</button>
    </div>

    {/* 🔹 Shops Section */}
      {!selectedShop && (
        <>
          <h3>Available Shops</h3>
          {shops.map((shop) => (
            <div
              key={shop.id}
              style={{
                border: "1px solid gray",
                padding: "10px",
                margin: "10px",
                cursor: "pointer",
              }}
              onClick={() => loadServices(shop.id)}
            >
              <h4>{shop.shop_name}</h4>
              <p>{shop.address}</p>
            </div>
          ))}
        </>
      )}

      {/* 🔹 Services Section */}
      {selectedShop && (
        <>
          <button onClick={goBack}>⬅ Back to Shops</button>

          <h3>Services</h3>
          {services.map((service) => (
            <div
              key={service.id}
              style={{
                border: "1px solid blue",
                padding: "10px",
                margin: "10px",
              }}
            >
              <h4>{service.name}</h4>
              <p>₹{service.price}</p>
              <p>{service.duration} mins</p>
              <button onClick={() => loadSlots(service.id)}>
                View Slots
              </button>
            </div>
          ))}
        </>
      )}

      {/* 🔹 Slots Section */}
      {slots.length > 0 && (
        <>
          <h3>Available Slots</h3>
          {slots.map((slot) => (
            <div
              key={slot.slot_id}
              style={{
                border: "1px solid green",
                padding: "10px",
                margin: "10px",
              }}
            >
              <p>Date: {slot.date}</p>
              <p>
                {slot.start_time} - {slot.end_time}
              </p>
              <button onClick={() => bookSlot(slot.slot_id)}>
                Book
              </button>
            </div>
          ))}
        </>
      )}
    </>
  );
}

export default CustomerDashboard;