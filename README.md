# Book Spot 📚

**Book Spot** is a modern, full-featured e-commerce web application for browsing, purchasing, and managing books. Built with **Flask** and **SQLite**, it provides a seamless experience for both customers and administrators.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-green)

---

## 🚀 Features

### 🛒 For Customers
- **User Accounts**: Secure Sign-up, Login, and Profile management.
- **Dynamic Catalog**: Browse books with advanced filtering (Category, Price, Author, Stock).
- **Smart Search**: Real-time search by title, author, or description.
- **Shopping Cart**: AJAX-powered cart with instant updates, quantity adjustment, and coupon support.
- **Secure Checkout**:
    - Multi-step checkout process.
    - Saved delivery addresses.
    - Automated stock validation.
    - **Email Notifications** for order confirmation.
- **User Dashboard**: View order history, recommendations, and account stats.

### 🛡️ For Administrators
- **Admin Dashboard**: Overview of key metrics (Sales, Users, Inventory).
- **Inventory Management**: Track low-stock items.
- **Order Management**: View and process customer orders. (In Progress)
- **User Management**: Monitor registered users.

---

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Bootstrap 5, Custom CSS
- **Icons**: Bootstrap Icons, FontAwesome
- **Templating**: Jinja2

---

## 📂 Project Structure

```
BookSpot/
├── app.py                  # Main Flask application entry point
├── config.py               # Configuration settings
├── schema.sql              # Database schema definition
├── requirements.txt        # Python dependencies
├── bookstore.db            # SQLite Database (generated)
├── static/                 # Static assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files (main.js, catalog.js)
│   └── images/             # Book images and assets
├── templates/              # HTML Templates (Jinja2)
│   ├── admin/              # Admin-related templates
│   ├── base.html           # Base layout template
│   ├── index.html          # Homepage
│   ├── catalog.html        # Product catalog
│   ├── product_details.html# Single product view
│   ├── cart.html           # Shopping cart
│   ├── checkout.html       # Checkout page
│   └── ...
└── utils/                  # Helper modules
    ├── db_helper.py        # Database connection utilities
    ├── helper.py           # General formatting helpers
    └── category_mapper.py  # Category logic handling
```

---

## ⚡ Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1.  **Clone the repository** (or extract zip):
    ```bash
    git clone https://github.com/yourusername/book-spot.git
    cd book-spot
    ```

2.  **Create a Virtual Environment**:
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database**:
    The application checks for the database on startup, but you can force initialization:
    ```bash
    python init_db.py
    ```
    *(Optional: Run `init_users.py` to seed default users if available)*

5.  **Run the Application**:
    ```bash
    python app.py
    ```

6.  **Access the App**:
    Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 📖 Usage Guide

### Customer Flow
1.  **Sign Up/Login**: Create an account to unlock shopping features.
2.  **Browse**: Use the Catalog page to filter books by Genre, Price, or Availability.
3.  **Cart**: Add books to your cart. Apply coupon codes like `BOOK20` or `FIRST100`.
4.  **Checkout**: Proceed to checkout, enter shipping details, and place your order.
5.  **Track**: View your order status in the Dashboard.

### Admin Flow
1.  **Login**: Access the Admin Login page (e.g., `/admin/login`).
2.  **Dashboard**: Monitor sales and inventory health.
3.  **Manage**: Use the provided tools to update catalog or users.

---

## 🗄️ Database Schema

The SQLite database consists of the following key tables:
- **users**: Customer account details.
- **admins**: Administrator account details.
- **books**: Inventory data (Title, Author, Price, Stock, etc.).
- **orders**: Order summaries and status.
- **order_items**: Line items linked to orders.
- **delivery_addresses**: Shipping info for orders.

---

## 🤝 Contributing

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Designed for Capstone Project by Shayan.*
