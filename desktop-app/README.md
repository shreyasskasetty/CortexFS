# CortexFS Frontend Setup

The frontend for CortexFS is built using ElectronJS, providing a native cross-platform desktop application that interacts with the backend to deliver an intuitive file organization experience. This document explains how to set up and run the frontend.

---

## Prerequisites

Ensure the following are installed on your system:

1. **Node.js** (16.x or higher)
2. **npm** (Node Package Manager, comes with Node.js)

---

## Setup Instructions

### Step 1: Clone the Frontend Repository

```bash
git clone https://github.com/shreyasskasetty/CortexFS.git
cd frontend
```

### Step 2: Install Dependencies
Run the following command to install all the required dependencies for the frontend:
```bash
npm install
```

### Step 3: Start the Frontend
```bash
npm run dev
```

### Notes:
* Ensure the backend is running before starting the frontend to avoid connectivity issues.
* For custom builds or configurations, modify the `electron-builder` settings in the `package.json` file.