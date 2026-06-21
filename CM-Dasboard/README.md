<div align="center">

# 🔥 GovConnect

**A Next-Generation, Real-Time Civic Engagement & Complaint Management Platform**

[![React](https://img.shields.io/badge/React-18-blue.svg?style=for-the-badge&logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg?style=for-the-badge&logo=postgresql)](https://postgresql.org/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-Real%20Time-black.svg?style=for-the-badge&logo=socket.io)](https://socket.io/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)

*Empowering citizens. Enabling administrators. Bridging the gap with seamless, real-time technology.*

</div>

<br />

GovConnect is a premium, full-stack SaaS application designed to revolutionize municipal complaint management. Built with a high-performance **FastAPI** backend and a beautifully responsive **React** frontend, it features role-based routing, military-grade JWT security, and instantaneous real-time updates via **Socket.IO**. 

---

## 📸 Core Features

- **🔐 Robust Authentication:** Secure Login/Signup with an advanced Access + Refresh token architecture.
- **👥 Role-Based Access Control (RBAC):** Dedicated, secure dashboards tailored for Citizens and Administrators.
- **🚀 Real-Time Event Engine:** Instantaneous UI updates using Socket.IO—no manual page refreshes required.
- **📝 Intelligent Complaint Tracking:** End-to-end lifecycle management from submission to resolution.
- **🛡️ Enterprise Security:** Rate-limiting, CORS locking, Helmet-style security headers, and strict input validation.
- **🎨 Premium UI/UX:** A modern, Apple/AWS-inspired design system utilizing Glassmorphism, smooth Framer Motion animations, and React Hot Toast notifications.

---

## 🏗️ Architecture Overview

GovConnect employs a decoupled, event-driven architecture to ensure scalability and responsiveness.

1. **Frontend (React/Vite):** Manages user state, caching (React Query), and rendering. Interacts with the backend via a centralized Axios instance.
2. **Backend (FastAPI):** Serves as the central nervous system. Handles business logic, RBAC, and integrates a dual ASGI wrapper to multiplex HTTP and WebSocket traffic.
3. **Database (PostgreSQL / SQLite):** Asynchronous database access via SQLAlchemy, ensuring high throughput and non-blocking I/O.
4. **Real-Time Layer (Socket.IO):** The Python backend emits targeted events (`newComplaint`, `statusUpdated`) to secure, user-specific or role-specific rooms, instantly syncing the React UI.

---

## ⚙️ Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React (Vite), TailwindCSS, Framer Motion | Fast, responsive, and animated user interfaces |
| **State/API** | React Query, Axios | Efficient data fetching, caching, and interception |
| **Backend** | FastAPI (Python), Uvicorn | High-performance, asynchronous REST API |
| **Database** | PostgreSQL, SQLAlchemy (Async) | Reliable, relational data storage with ORM |
| **Real-Time** | Socket.IO (Client + Python Server) | Bidirectional event-based communication |
| **Security** | JWT, Passlib (Bcrypt), Python-Jose | Token generation, hashing, and decryption |

---

## 🔐 Authentication Flow

GovConnect implements a secure, state-of-the-art dual-token system:

1. **Login:** User authenticates and receives a short-lived **Access Token** (15 mins) and a long-lived **Refresh Token** (7 days).
2. **Storage:** The Access Token is stored securely in memory/localStorage. The Refresh Token is stored as an `httpOnly`, `Secure`, `SameSite=Lax` cookie to prevent XSS attacks.
3. **Interception:** Axios automatically attaches the Access Token to every request.
4. **Auto-Renewal:** If a `401 Unauthorized` occurs, the Axios interceptor transparently calls the `/auth/refresh` endpoint using the secure cookie, retrieves a new Access Token, and retries the failed request seamlessly.

---

## 🔄 Real-Time System

Socket.IO is deeply integrated into the application stack:

- **Secured Handshake:** Connections require a valid JWT. Unauthenticated sockets are instantly rejected.
- **Smart Rooms:** 
  - Admins join a global `"admins"` room.
  - Citizens join a private room based on their `user_id`.
- **Event Dispatching:**
  - `newComplaint`: Emitted to the `"admins"` room when a citizen submits a ticket. Triggers a toast and table refetch on the Admin Dashboard.
  - `statusUpdated`: Emitted to a specific citizen's room when an admin updates their ticket. Triggers a toast and dashboard refetch for that specific citizen.

---

## 📁 Folder Structure

```text
CM-Dasboard/
├── app/                      # FastAPI Backend
│   ├── api/                  # Route controllers & Socket.IO logic
│   ├── core/                 # Config, security, and JWT utilities
│   ├── db/                   # SQLAlchemy async engine & sessions
│   ├── models/               # Database schemas
│   ├── schemas/              # Pydantic validation models
│   └── main.py               # Application entry point & middleware
├── frontend/                 # React Frontend
│   ├── src/
│   │   ├── components/       # Reusable UI elements & Layouts
│   │   ├── context/          # AuthContext & global state
│   │   ├── pages/            # View components (Admin/Citizen Dashboards)
│   │   └── services/         # Axios instance, React Query hooks, Socket.js
│   ├── vite.config.js
│   └── package.json
└── .env.example              # Environment variable template
```

---

## 🚀 Getting Started

Follow these steps to run GovConnect locally.

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/govconnect.git
cd govconnect/CM-Dasboard
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server (FastAPI + Socket.IO)
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173` and the backend at `http://localhost:8000`.

---

## 🌍 Environment Variables Example

Create a `.env` file in the root directory:

```env
# Database Settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=complaint_db

# App Settings
SECRET_KEY=YOUR_SUPER_SECRET_KEY
REFRESH_SECRET_KEY=YOUR_REFRESH_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=15

# SQLite Toggle (Set to true for local testing without PostgreSQL)
USE_SQLITE=true
```

---

## 🧪 API Overview

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/signup` | Register a new user | Public |
| `POST` | `/api/v1/auth/login` | Authenticate and receive tokens | Public |
| `POST` | `/api/v1/auth/refresh` | Renew access token via cookie | Public |
| `POST` | `/api/v1/complaints/` | Submit a new complaint | Citizen |
| `GET` | `/api/v1/complaints/my-complaints` | Get user's complaints | Citizen |
| `GET` | `/api/v1/admin/complaints` | Get all complaints | Admin |
| `PATCH` | `/api/v1/admin/complaints/{id}` | Update complaint status | Admin |

---

## 🔒 Security Features

- **Cross-Origin Resource Sharing (CORS):** Strictly limited to frontend origins with credentials enabled.
- **Helmet Headers:** Mitigation against XSS, clickjacking, and MIME-sniffing.
- **Rate Limiting:** IP-based throttling (100 requests / 15 mins) to prevent DDoS and brute-force attacks.
- **Input Validation:** Strict parsing and sanitization using Pydantic schemas.
- **HttpOnly Cookies:** Refresh tokens are shielded from JavaScript access, preventing XSS token theft.

---

## 🎨 UI/UX Highlights

- **Glassmorphism Design:** Beautiful frosted-glass effects on topbars and modals.
- **Micro-Interactions:** Hover lifts, tap shrinks, and dynamic color transitions.
- **Intelligent Layouts:** Responsive sidebars that convert to animated sliding drawers on mobile.
- **Toast Notifications:** Sleek, non-intrusive alerts for real-time events and system errors.
- **Loading Skeletons:** Smooth data-fetching experiences utilizing React Query's `isLoading` states.

---

## 📊 Future Improvements

- **AI Auto-Classification:** Integrate NLP to automatically route complaints to the correct department based on description.
- **Advanced Analytics Dashboard:** Add heatmaps for complaint geographic clustering.
- **Push Notifications:** Implement PWA service workers for mobile push alerts.
- **Multi-Language Support:** Expand accessibility with i18n localization.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

<div align="center">
  <p>Built with ❤️ by an Engineer</p>
</div>
