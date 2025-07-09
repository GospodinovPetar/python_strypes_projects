# djangoMeetups 🎉

Welcome to **DjangoMeetups**! 🚀 This is a simple yet powerful Django project designed to help users find, sign up for, and even request their own meetups. It’s built with Django, using an SQLite database, and adds a little extra flair with an email notification system for meetup requests. 

### Features:
- **Meetups Management**: Admins can create and manage meetups.
- **Signup**: People can sign up for a meetup by providing their email address.
- **Request a Meetup**: Users can request a new meetup by filling out a form. Once submitted, you’ll get an email with the details! (Implemented by yours truly 😉)
  
## 🚀 Getting Started

### Prerequisites

You’ll need a few things before you start:

- Python 3.x
- Django 3.x (or higher)
- SQLite (default database used in this project)

### Install & Set Up

1. **Clone or download the project**:
   ```bash
   git clone https://github.com/GospodinovPetar/python_strypes_projects.git
   ```

2. **Go to the project directory**:
   ```bash
   cd django_course_site
   ```

3. **Install dependencies**:
   This project has a `requirements.txt` file to install all the packages you need:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   Now, let's set up the database (it’s an SQLite database by default):
   ```bash
   python manage.py migrate
   ```

### 🎉 Running the Server

Now you're ready to run the app!

Start the Django development server:
```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser to see the app in action.

## 📧 Request a Meetup

One cool feature I added is the ability for users to **request a meetup**! 🎉  
Using Formspree, users can send a request with the meetup’s details, and you’ll get an email with all the information. Here’s how it works:

1. Navigate to the "Request a Meetup" page on the website.
2. Fill out the form with your meetup details.
3. Hit submit, and boom! The meetup request is sent to your inbox via email. 📬

This ensures everything is set up and working as expected!

## 📝 License

This project is licensed under the MIT License. Feel free to use, modify, and share it!

---

Enjoy building with **djangoMeetups**! If you have any questions or run into any issues, don’t hesitate to reach out. Happy coding! 🙌💻✨
```