// ===============================
// Authentication utilities
// ===============================
const API_BASE_URL = window.location.origin;

class AuthService {
  static async checkAuth() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/check-session`, {
        credentials: "include"
      });

      return await response.json();
    } catch (error) {
      console.error("Auth check failed:", error);
      return { authenticated: false };
    }
  }

  static async signin(role, email, password) {
    const response = await fetch(`${API_BASE_URL}/api/auth/signin`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ role, email, password }),
    });

    return await response.json();
  }

  static async signout() {
    const response = await fetch(`${API_BASE_URL}/api/auth/signout`, {
      method: "POST",
      credentials: "include",
    });

    return await response.json();
  }

  static async updateProfile(data) {
    const response = await fetch(`${API_BASE_URL}/api/user/update-profile`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    return await response.json();
  }
}

// ===============================
// Navbar Authentication Rendering
// ===============================
document.addEventListener("DOMContentLoaded", async function () {

  const navAuth = document.getElementById("navAuth");
  if (!navAuth) return;

  const authState = await AuthService.checkAuth();

  if (authState.authenticated) {

    const user = authState.user;
    const role = authState.role;

    let initials = "";

    if (role === "student") {
      initials = (user.first_name[0] + user.last_name[0]).toUpperCase();
    }
    else if (role === "company") {
      initials = user.company_name.substring(0, 2).toUpperCase();
    }
    else {
      initials = user.name
        .split(" ")
        .map(n => n[0])
        .join("")
        .toUpperCase();
    }

    navAuth.innerHTML = `
      <div class="user-dropdown">
        <button class="user-avatar">${initials}</button>
        <div class="dropdown-content">
            <a href="#" id="dashboardLink">Dashboard</a>
            <a href="/auth/account-settings.html">Account Settings</a>
            <a href="#" id="signoutBtn">Sign Out</a>
        </div>
      </div>
    `;

    setupDropdown(role);

  } else {

    navAuth.innerHTML = `
      <button class="btn-signup" onclick="window.location.href='/auth/student-signup.html'">
        Sign Up
      </button>
      <button class="btn-signin" onclick="window.location.href='/auth/signin.html'">
        Sign In
      </button>
    `;
  }
});

// ===============================
// Dropdown + Dashboard Redirect
// ===============================
function setupDropdown(role) {

  const avatar = document.querySelector(".user-avatar");
  const dropdown = document.querySelector(".dropdown-content");

  if (!avatar || !dropdown) return;

  avatar.addEventListener("click", e => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
  });

  document.addEventListener("click", () => {
    dropdown.classList.remove("show");
  });

  // Dashboard redirect by role
  const dashboardLink = document.getElementById("dashboardLink");

  if (dashboardLink) {
    dashboardLink.addEventListener("click", () => {

      if (role === "student")
        window.location.href = "/student-dashboard.html";

      else if (role === "company")
        window.location.href = "/company-dashboard.html";

      else
        window.location.href = "/admin-dashboard.html";
    });
  }

  // Signout handler
  const signoutBtn = document.getElementById("signoutBtn");

  if (signoutBtn) {
    signoutBtn.addEventListener("click", async e => {
      e.preventDefault();

      await AuthService.signout();

      localStorage.removeItem("vternship_user");
      localStorage.removeItem("vternship_role");

      window.location.href = "/index.html";
    });
  }
}

// ===============================
// Utility Validators
// ===============================
function validateEmail(email) {
  const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return re.test(email);
}

function validatePassword(password) {
  return password.length >= 8;
}

// ===============================
// Toast Notification System
// ===============================
function showToast(message, type = "info") {

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    z-index: 9999;
    animation: slideIn 0.3s ease;
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ===============================
// Toast Animations
// ===============================
const style = document.createElement("style");

style.textContent = `
@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOut {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}

.toast-success { border-left: 4px solid #22c55e; }
.toast-error { border-left: 4px solid #ef4444; }
.toast-info { border-left: 4px solid #6366f1; }
`;

document.head.appendChild(style);
