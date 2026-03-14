Barber Shop Booking System



A Full-Stack Barber Shop Booking System that allows customers to book appointments with barbers online and helps barbers manage their services, availability, and bookings through a dashboard.



This project solves a common problem in barber shops — long waiting times and unmanaged appointments — by providing an easy-to-use online booking platform.



Features

Authentication \& Authorization



User authentication system with secure login and registration



Role-based access control for Barbers and Customers



Appointment Booking



Customers can view available time slots



Book appointments with their preferred barber



Prevents double booking of slots



Barber Dashboard



Manage services offered by the shop



Control shop availability



View and manage customer bookings



Customer Interface



Browse available services



Select barber and preferred time slot



Book appointments easily



API System



Backend built using RESTful APIs



Frontend communicates with backend using Axios



Tech Stack

Frontend



React



Axios



CSS



Backend



Flask (Python)



REST APIs



Database



PostgreSQL



Deployment



Frontend: Render



Backend: Render



Project Structure

barber-shop-booking-system

│

├── frontend

│   ├── components

│   ├── pages

│   ├── services

│   └── App.js

│

├── backend

│   ├── routes

│   ├── models

│   ├── config

│   └── app.py

│

└── README.md

API Endpoints 

Method	Endpoint	Description

POST	/api/register	Register new user

POST	/api/login	Login user

GET	/api/services	Get all services

POST	/api/book	Book appointment

GET	/api/bookings	Get user bookings

Installation

1 Clone the repository

git clone https://github.com/ramansinghraghav/Barber-shop-booking-system.git

2 Backend Setup

cd backend

pip install -r requirements.txt

python app.py

3 Frontend Setup

cd frontend

npm install

npm start

Future Improvements



Payment Integration



Notifications for bookings



Barber rating \& review system



Admin panel for shop management



Project Purpose



This project was built to practice and demonstrate:



Full-stack web development



REST API development



Frontend–backend integration



Authentication systems



Real-world problem solving

