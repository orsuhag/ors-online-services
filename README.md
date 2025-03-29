# ORS - Online Services
#### Video Demo:  <https://youtu.be/LjpdOsJcAsc>
#### Live Render:  <https://ors-online-services.onrender.com>
#### Description:
This project is a web application. It mainly consists of the framework named **Flask**. It has four board sections.
The first three sections are different kinds of services. But the last one is the payment system to engage these services.
They are -

1. Accommodation
2. Consultancy
3. Transportation
4. Payment

Users must register to provide or engage services. There are defined **flask** routes and **HTML** documents to
access and explore these services. Users have two groups to interact with each other. They are -

1. Provider
2. Customer

Providers can do the following actions -

- Add Service
- Edit Service
- Empty Service
- Delete Service

Customers can do the following actions -

- Engage Service

Users can request the following transactions -

- Receive Request
- Send Request
- Deposit Request
- Withdraw Request

There is also a route for admin. It helps the admin to manage payment transactions. Admin can modify the
transactions of deposit and withdraw requests only. Admin can confirm deposit requests based on transaction-ID
of a bank transfer from the user bank account to the admin bank account. Admin can also insert transaction-ID of a
bank transfer from admin bank account to the user bank account for withdraw request. Then users ensure the withdrawal
request.
