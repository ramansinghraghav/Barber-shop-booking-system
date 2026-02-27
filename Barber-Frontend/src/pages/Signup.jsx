import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";

function Signup() {
  const [role, setRole] = useState("customer");

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const [shopName, setShopName] = useState("");
  const [address, setAddress] = useState("");
  const [openTime, setOpenTime] = useState("");
  const [closeTime, setCloseTime] = useState("");
  const [capacity, setCapacity] = useState("");

  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      await API.post("/api/signup", {
        name,
        phone,
        password,
        role,
        shop_name: role === "barber" ? shopName : null,
        address: role === "barber" ? address : null,
        open_time: role === "barber" ? openTime : null,
        close_time: role === "barber" ? closeTime : null,
        capacity: role === "barber" ? capacity : null
      });

      alert("Signup Successful ✅");
      navigate("/");
    } catch (err) {
      alert("Signup Failed ❌");
      console.log(err);
    }
  };

  return (
    <div>
      <h2>Signup</h2>

      <select onChange={(e) => setRole(e.target.value)}>
        <option value="customer">Customer</option>
        <option value="barber">Shop Owner</option>
      </select>

      <input placeholder="Name" onChange={(e) => setName(e.target.value)} />
      <input placeholder="Phone" onChange={(e) => setPhone(e.target.value)} />
      <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />

      {role === "barber" && (
        <>
          <h3>Shop Details</h3>
          <input placeholder="Shop Name" onChange={(e) => setShopName(e.target.value)} />
          <input placeholder="Address" onChange={(e) => setAddress(e.target.value)} />
          <input placeholder="Open Time (09:00)" onChange={(e) => setOpenTime(e.target.value)} />
          <input placeholder="Close Time (18:00)" onChange={(e) => setCloseTime(e.target.value)} />
          <input placeholder="Capacity (No of customers per slot)" onChange={(e) => setCapacity(e.target.value)} />
        </>
      )}

      <button onClick={handleSignup}>Signup</button>
    </div>
  );
}

export default Signup;