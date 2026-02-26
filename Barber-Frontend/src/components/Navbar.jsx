import { useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    navigate("/");
  };

  return (
    <div style={{
      display: "flex",
      justifyContent: "space-between",
      padding: "15px",
      background: "#222",
      color: "white"
    }}>
      <h3 style={{cursor:"pointer"}} onClick={() => navigate("/")}>
        Barber Booking
      </h3>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

export default Navbar;