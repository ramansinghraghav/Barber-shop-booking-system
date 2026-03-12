import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";

function Login() {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await API.post("/api/login",Date, {
        phone,
        password,
      });

      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("user", JSON.stringify(res.data.user));

      if (res.data.user.role === "customer") {
        navigate("/customer");
      } else {
        navigate("/barber");
      }

    } catch (err) {
      alert("Login Failed ❌");
      console.log(err);
    }
  };

  return (
    <div>
      <h2>Login</h2>

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

      <button onClick={handleLogin}>Login</button>
        <p>
        Don't have an account?{" "}
        <span
        style={{ color: "blue", cursor: "pointer" }}
        onClick={() => navigate("/signup")}
        >
        Sign Up
    </span>
    </p>
    </div>
  );
}

export default Login;