import { useState } from "react";
import { loginUser } from "../services/api";

function Login() {
  const [phone, setPhone] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    const data = await loginUser(phone);

    if (data.success) {
      localStorage.setItem("token", data.token);
      alert("Login successful");
      window.location.href = "/dashboard";
    } else {
      alert(data.message);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h2>Login</h2>

      <input
        type="text"
        placeholder="Phone number"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
      />

      <button type="submit">Login</button>
    </form>
  );
}

export default Login;
