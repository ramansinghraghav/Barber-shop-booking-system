const API = "http://127.0.0.1:5000";
const token = localStorage.getItem("token");

/* ---------- Navigation ---------- */
function goServices() {
  window.location.href = "services.html";
}
function login() {
    alert("Login function working ✅");
}

function login() {
  console.log("login() called");

  fetch(API + "/api/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      phone: document.getElementById("phone").value
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("LOGIN RESPONSE:", data);

    if (data.success) {
      localStorage.setItem("token", data.token);
      window.location.href = "./dashboard";
    } else {
      alert(data.message || "Login failed");
    }
  })
  .catch(err => {
    console.error("LOGIN ERROR:", err);
  });
}
function checkLogin() {
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/login";
    }
}
function loadServices() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    fetch("/api/services", {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById("services");
        container.innerHTML = "";

        if (!data.services || data.services.length === 0) {
            container.innerHTML = "<p>No services available</p>";
            return;
        }

        data.services.forEach(service => {
            const div = document.createElement("div");
            div.style.border = "1px solid #ccc";
            div.style.padding = "10px";
            div.style.margin = "10px 0";

            div.innerHTML = `
                <h3>${service.name}</h3>
                <p>Price: ₹${service.price}</p>
                <p>Duration: ${service.duration} mins</p>
                <button onclick="viewSlots(${service.id})">View Slots</button>
            `;

            container.appendChild(div);
        });
    })
    .catch(err => {
        console.error(err);
        alert("Failed to load services");
    });
}
function viewSlots(serviceId) {
    window.location.href = `/slots?service_id=${serviceId}`;
}

function goSlots() {
  const serviceId = localStorage.getItem("service_id");
  if (!serviceId) {
    alert("Please select a service first");
    return;
  }
  window.location.href = "slots.html";
}
function goBookings() {
  alert("Bookings page next step 😄");
}

/* ---------- Load Services ---------- */
if (document.getElementById("services")) {
  fetch(API + "/api/services", {
    headers: {
      "Authorization": "Bearer " + token
    }
  })
  .then(res => res.json())
  .then(data => {
    const div = document.getElementById("services");
    data.services.forEach(s => {
      div.innerHTML += `
        <div style="border:1px solid #ccc; padding:10px; margin:10px">
          <h4>${s.name}</h4>
          <p>₹${s.price} | ${s.duration} min</p>
          <button onclick="selectService(${s.id})">View Slots</button>
        </div>
      `;
    });
  });
}

function login() {
    const phone = document.getElementById("phone").value;

    if (!phone) {
        alert("Phone number required");
        return;
    }

    fetch("/api/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ phone: phone })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // 🔐 TOKEN SAVE
            localStorage.setItem("token", data.token);

            // 🚀 REDIRECT
            window.location.href = "/dashboard";
        } else {
            alert(data.message || "Login failed");
        }
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

function selectService(id) {
  localStorage.setItem("service_id", id);
  window.location.href = "slots.html";
}

/* ---------- Load Slots ---------- */
if (document.getElementById("slots")) {
  const serviceId = localStorage.getItem("service_id");

  fetch(API + "/api/slots/" + serviceId, {
    headers: {
      "Authorization": "Bearer " + token
    }
  })
  .then(res => res.json())
  .then(data => {
    const div = document.getElementById("slots");
    data.slots.forEach(s => {
      div.innerHTML += `
        <div style="border:1px solid #aaa; padding:10px; margin:10px">
          <p>${s.date} | ${s.start_time} - ${s.end_time}</p>
          <button onclick="bookSlot(${s.slot_id})">Book</button>
        </div>
      `;
    });
  });
}

function bookSlot(slotId) {
  fetch(API + "/api/book-slot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify({ slot_id: slotId })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message);
    window.location.reload();
  });
}
function goOrders() {
    window.location = "/orders";
}

function goProfile() {
    window.location = "/profile";
}
function goToPage(path) {
    window.location.href = path;
}

