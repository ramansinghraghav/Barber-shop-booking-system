const API_BASE = "http://127.0.0.1:5000";

export async function loginUser(phone) {
  const response = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ phone })
  });

  return response.json();
}
