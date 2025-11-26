document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const manageSection = document.getElementById("manage-section");
  const manageMessage = document.getElementById("manage-message");
  const createForm = document.getElementById("create-form");
  const manageActivities = document.getElementById("manage-activities");

  function showMessage(el, text, kind = "success") {
    el.textContent = text;
    el.className = kind;
    el.classList.remove("hidden");
    setTimeout(() => el.classList.add("hidden"), 4000);
  }

  function getAuthHeader() {
    return sessionStorage.getItem("authToken");
  }

  async function fetchActivities() {
    try {
      const res = await fetch("/activities");
      const activities = await res.json();
      renderManageActivities(activities);
    } catch (err) {
      manageActivities.textContent = "Failed to load activities.";
    }
  }

  function renderManageActivities(activities) {
    manageActivities.innerHTML = "";
    const list = document.createElement("div");
    Object.keys(activities).forEach((name) => {
      const card = document.createElement("div");
      card.className = "activity-card";
      const h4 = document.createElement("h4");
      h4.textContent = name;
      const del = document.createElement("button");
      del.textContent = "Delete";
      del.addEventListener("click", () => deleteActivity(name));
      card.appendChild(h4);
      card.appendChild(del);
      list.appendChild(card);
    });
    manageActivities.appendChild(list);
  }

  async function deleteActivity(name) {
    const token = getAuthHeader();
    if (!token) return showMessage(manageMessage, "Not authenticated", "error");

    try {
      const res = await fetch(`/activities/${encodeURIComponent(name)}`, {
        method: "DELETE",
        headers: {
          Authorization: token,
        },
      });

      const body = await res.json();
      if (res.ok) {
        showMessage(manageMessage, body.message, "success");
        fetchActivities();
      } else {
        showMessage(manageMessage, body.detail || "Error deleting", "error");
      }
    } catch (err) {
      showMessage(manageMessage, "Network error", "error");
    }
  }

  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const token = "Basic " + btoa(`${username}:${password}`);

    // Try a simple authenticated request to verify credentials
    fetch("/activities", { headers: { Authorization: token } })
      .then((r) => {
        if (r.status === 401) throw new Error("Unauthorized");
        // success
        sessionStorage.setItem("authToken", token);
        loginForm.reset();
        manageSection.classList.remove("hidden");
        showMessage(loginMessage, "Logged in successfully", "success");
        fetchActivities();
      })
      .catch(() => {
        showMessage(loginMessage, "Login failed", "error");
      });
  });

  createForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("act-name").value;
    const desc = document.getElementById("act-desc").value;
    const schedule = document.getElementById("act-schedule").value;
    const max = parseInt(document.getElementById("act-max").value, 10);
    const token = getAuthHeader();
    if (!token) return showMessage(manageMessage, "Not authenticated", "error");

    const params = new URLSearchParams({
      activity_name: name,
      description: desc,
      schedule: schedule,
      max_participants: String(max),
    });

    try {
      const res = await fetch(`/activities?${params.toString()}`, {
        method: "POST",
        headers: { Authorization: token },
      });
      const body = await res.json();
      if (res.ok) {
        showMessage(manageMessage, body.message, "success");
        createForm.reset();
        fetchActivities();
      } else {
        showMessage(manageMessage, body.detail || "Error creating", "error");
      }
    } catch (err) {
      showMessage(manageMessage, "Network error", "error");
    }
  });

  // Expose a logout for convenience
  window.adminLogout = function () {
    sessionStorage.removeItem("authToken");
    manageSection.classList.add("hidden");
    showMessage(loginMessage, "Logged out", "success");
  };
});
