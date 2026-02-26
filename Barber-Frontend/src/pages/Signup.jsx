import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";

function Signup() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("customer");

  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      await API.post("/api/signup", {
        name,
        phone,
        password,
        role,
      });

      alert("Signup successful ✅");
      navigate("/");

    } catch (err) {
      alert("Signup failed ❌");
      console.log(err);
    }
  };

  return (
    <div>
      <h2>Signup</h2>

      <input
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <input
        placeholder="Phone"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="customer">Customer</option>
        <option value="barber">Barber</option>
      </select>

      <button onClick={handleSignup}>Signup</button>

      <p
        onClick={() => navigate("/")}
        style={{ cursor: "pointer", color: "blue" }}
      >
        Already have account? Login
      </p>
    </div>
  );
}

export default Signup;