import { useEffect, useState } from "react";
import API from "../api/axios";

function CustomerDashboard() {
  const [services, setServices] = useState([]);
  const [slots, setSlots] = useState([]);
  const [selectedService, setSelectedService] = useState(null);

  useEffect(() => {
    API.get("/api/services")
      .then((res) => {
        setServices(res.data.services);
      })
      .catch((err) => {
        console.log(err);
        alert("Failed to load services");
      });
  }, []);

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

      // reload slots
      loadSlots(selectedService);
    } catch (err) {
      alert("Slot already booked ❌");
    }
  };

  return (
    <div>
      <h2>Customer Dashboard</h2>

      <h3>Services</h3>
      {services.map((service) => (
        <div key={service.id} style={{ border: "1px solid gray", padding: "10px", margin: "10px" }}>
          <h4>{service.name}</h4>
          <p>Price: ₹{service.price}</p>
          <p>Duration: {service.duration} mins</p>
          <button onClick={() => loadSlots(service.id)}>
            View Slots
          </button>
        </div>
      ))}

      {slots.length > 0 && (
        <>
          <h3>Available Slots</h3>
          {slots.map((slot) => (
            <div key={slot.slot_id} style={{ border: "1px solid blue", padding: "10px", margin: "10px" }}>
              <p>Date: {slot.date}</p>
              <p>Time: {slot.start_time} - {slot.end_time}</p>
              <button onClick={() => bookSlot(slot.slot_id)}>
                Book</button>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

export default CustomerDashboard;