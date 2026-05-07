# 🚀 Aidora Backend System

A collaborative, robust backend system built with **Django REST Framework** designed to streamline humanitarian aid operations. It acts as the central bridge connecting **Organizations**, **Volunteers**, and **Refugees**, ensuring secure, role-based access to services and real-time task management.

---

## 📋 Table of Contents
- [Team & Contribution](#-team--contribution)
- [Database Schema](#-database-schema)
- [Project Overview](#-project-overview)
- [Tech Stack](#-tech-stack)
- [Authentication & Authorization](#-authentication--authorization)
- [Key Features](#-key-features--architecture)
- [Technical Challenges](#-technical-challenges--solutions)
- [Workflow](#-workflow-diagram)
- [Getting Started](#-getting-started)

---

## 👥 Team & Contribution

This project was developed collaboratively, with responsibilities divided to ensure clean separation of concerns:

*   **Siedra-Ziedan:**
    - Responsible for **Accounts**, **Organizations**, and **Requests** modules
    - Implemented CRUD operations for volunteers and organizations
    - Designed user structure and initial UI interfaces
    - **Authentication Core:** Configured JWT (Access & Refresh tokens) with custom login logic
    - **Security & Automation:** Engineered PIN system with automated email notifications on volunteer approval
    - **State Management:** Developed `/api/auth/me/` endpoint for intelligent frontend routing
    - **Database Architecture:** Designed and optimized schema for scalability
    - Developed the real-time notifications infrastructure for Organizations, enabling automated alerts for volunteer approvals and task status tracking.
*   **Shahd-Ibraheem :**
    - Responsible for **Refugees** module and service request 
    - Implemented all CRUD operations for refugee profiles
    - **QR Code Scanning Workflow:** Developed secure QR scanning system to validate request completion
    - Integrated backend with Flutter mobile application
    - Implemented real-time notifications 

---

## 📊 Database Schema

**ER Diagram:** [View ER_Diagram.pdf](ER_Diagram.pdf)

The database is architected to support three primary user roles with role-based access control (RBAC):

---


## 🧠 Project Overview
Aidora manages the lifecycle of humanitarian aid. It handles the journey from a refugee requesting aid to a volunteer completing the task via a secure QR scan. The system emphasizes **security**, **automated notifications**, and **dynamic state management** for a seamless mobile experience.

---

## ⚙️ Tech Stack
- **Backend Framework:** Django / Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Authentication:** JWT (JSON Web Tokens) with `djangorestframework-simplejwt`
- **File Handling:** Pillow (Image uploads)
- **Architecture:** Clean Architecture (Partial), Class-Based Views (ViewSets)

---

## 🔐 Authentication & Authorization

### JWT Configuration
The authentication system uses `djangorestframework-simplejwt` for secure token management:

- **Access Token:** Short-lived token (default: 5 minutes) for protected endpoint access
- **Refresh Token:** Long-lived token (default: 24 hours) to obtain new access tokens without re-authentication
- **Login Response:** Includes `role` identifier for immediate frontend user type detection

### The Auth/Me Endpoint Strategy

The `/api/auth/me/` endpoint serves as the routing brain for the frontend application. It returns a dynamic JSON response:

```json
{
  "role": "volunteer",
  "profile_completed": false,
  "application_status": "pending"
}
```

**Field Definitions:**
- `role`: One of `organization`, `volunteer`, or `refugee`
- `profile_completed`: Boolean indicating profile setup completion
- `application_status`: Volunteer-specific field (`null`, `pending`, `approved`, `rejected`)

### Frontend Routing Logic

**Volunteer Flow:**
| Status | Display |
|--------|---------|
| `application_status: null` | Show application form |
| `application_status: pending` | Show "Application Under Review" screen |
| `application_status: rejected` | Show rejection details & reapply option |
| `application_status: approved` + `PIN not verified` | Show "Enter PIN" verification |
| `application_status: approved` + `profile_completed: true` | Show volunteer dashboard |

**Refugee Flow:**
| Status | Display |
|--------|---------|
| `profile_completed: false` | Show "Complete Profile" form |
| `profile_completed: true` | Show home screen & service request interface |

---

## 🧩 Key Features & Architecture

### 1. **Role-Based Access Control (RBAC)**
Three distinct user roles with specialized permissions:

| Role | Capabilities |
|------|---|
| **Organization** | Manage volunteer applications, approve/reject requests, create tasks, send notifications |
| **Volunteer** | Apply to organizations, receive task assignments, scan QR codes, rate organizations |
| **Refugee** | Create service requests, upload profile documents, track request status, interact with volunteers |

### 2. **Automated PIN & Email System**
Security-first approach to verify volunteer identity:

1. Organization approves volunteer application
2. Signal automatically triggers PIN generation (4-digit code)
3. Email notification sent to volunteer with PIN
4. Volunteer verifies PIN via `/api/auth/verify-pin/`
5. Profile unlocked, volunteer can accept tasks

### 3. **QR Code Scanning Workflow**
Ensures task completion occurs at physical location:

1. Organization approves refugee's service request → **Task** generated
2. Task assigned to matched volunteer
3. Volunteer receives notification & meets refugee
4. Volunteer scans **refugee's unique QR code** using mobile app
5. Backend validates QR and marks task as **`completed`**
6. Refugee receives completion notification
7. Volunteer gains ability to rate organization

### 4. **Performance Optimization**
Production-ready optimization patterns:

- **Pagination:** Implemented on all list endpoints for mobile efficiency
- **Query Optimization:** Strategic use of `select_related()` and `prefetch_related()`
- **Caching:** Frequently accessed data cached to reduce database load
- **Lazy Loading:** Profile images and documents loaded on-demand

---

## 🛠 Technical Challenges & Solutions

### Challenge 1: Dynamic Frontend Routing Based on Backend State
**Problem:** Flutter app needed to determine which screen to show based on complex state combinations (profile done? approved? PIN verified?).

**Solution:** 
- Built intelligent `/api/auth/me/` serializer that conditionally includes fields based on user role
- Volunteer-only fields (`application_status`) only returned for volunteer users
- Refugee-only logic prevents irrelevant data clutter on refugee clients
- State combinations map to exact UI screens without client-side complexity

**Implementation:**
```python
class AuthMeSerializer(serializers.ModelSerializer):
    application_status = serializers.SerializerMethodField()
    
    def get_application_status(self, obj):
        if obj.role == 'volunteer':
            return obj.volunteerapplication.status
        return None
```

### Challenge 2: Preventing Fraudulent Task Completion
**Problem:** Volunteers could claim task completion without actually being present with the refugee.

**Solution:**
- Implemented QR code validation system
- Refugee's unique QR code embedded in profile
- Task completion endpoint requires valid `qr_code_data`
- Backend validates QR matches refugee associated with task
- Only valid scans update task status to `completed`

**Security Flow:**
1. Volunteer scans refugee's QR code via mobile app
2. QR data sent to `/api/tasks/{id}/complete/`
3. Backend verifies QR belongs to refugee on this task
4. If valid → update task, notify refugee, unlock rating ability
5. If invalid → reject with error

### Challenge 3: Fair Rating & Review System
**Problem:** Volunteers/refugees could rate before completing interaction, leading to bias.

**Solution:**
- Added validation: ratings only allowed after `task.status == 'completed'`
- Timestamp recorded to prevent duplicate ratings
- Only participants in the task can submit ratings
- Rating endpoint checks task completion status first

**Validation Logic:**
```python
def create_rating(self, task_id, rater_id, rating):
    task = Task.objects.get(id=task_id)
    if task.status != 'completed':
        raise ValidationError("Task must be completed before rating")
    # Proceed with rating creation
```

---



## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- pip (Python package manager)

### Installation & Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/aidora-backend.git
cd aidora-backend
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Database

**Create PostgreSQL Database:**
```sql
CREATE DATABASE aidora_db;
CREATE USER aidora_user WITH PASSWORD 'your_secure_password';
ALTER ROLE aidora_user SET client_encoding TO 'utf8';
ALTER ROLE aidora_user SET default_transaction_isolation TO 'read_committed';
GRANT ALL PRIVILEGES ON DATABASE aidora_db TO aidora_user;
```

**Update Environment Settings:**
Create `.env` file in project root:
```env
DB_NAME=aidora_db
DB_USER=aidora_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_django_secret_key
DEBUG=True
```

#### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. Create Superuser (Admin Account)
```bash
python manage.py createsuperuser
```

#### 7. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### 8. Start Development Server
```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`
Admin panel: `http://localhost:8000/admin`

---

## 📱 API Documentation

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register/` | User registration |
| POST | `/api/auth/login/` | User login (returns JWT tokens) |
| GET | `/api/auth/me/` | Get current user profile & routing data |
| POST | `/api/auth/verify-pin/` | Verify volunteer PIN |
| POST | `/api/volunteers/applications/` | Submit volunteer application |
| GET | `/api/refugees/profile/` | Get refugee profile |
| POST | `/api/refugees/requests/` | Create service request |
| GET | `/api/organizations/` | List organizations |
| POST | `/api/tasks/{id}/complete/` | Mark task as completed (QR scan) |

---

## 🔗 External Resources

- **📱 Mobile App (Flutter):** [Aidora Flutter Repository](https://github.com/AsseadIbrahim/Aidora_flutter.git)
- **🎨 UI/UX Design (Figma):** [Aidora Design System](https://www.figma.com/design/GUgPRg89wodNHTfcDUgC4N/myproject?node-id=1071-281&t=vdtPJTrRQFsro4CL-1)
- **📊 Database Schema:** [ER_Diagram.pdf](ER_Diagram.pdf)

---

## 📝 Project Structure
```
Aidora/
├── accounts/              # User authentication & profiles
│   ├── models.py         # User, VolunteerProfile, RefugeeProfile
│   ├── views.py          # Auth endpoints
│   ├── serializers.py    # DRF serializers
│   └── signals.py        # PIN generation on approval
├── organizations/         # Organization management
│   ├── models.py         # Organization, Service
│   └── views.py          # Organization CRUD
├── requests/             # Service requests & tasks
│   ├── models.py         # Request, Task, Rating
│   └── views.py          # Task completion (QR scanning)
├── Aidora/              # Project settings
│   ├── settings.py      # Django configuration
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI configuration
├── manage.py            # Django CLI
├── requirements.txt     # Python dependencies
├── ER_Diagram.pdf       # Database schema diagram
└── README.md            # This file
```

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test accounts.tests
python manage.py test organizations.tests
python manage.py test requests.tests
```

---

## ⚙️ Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure CORS for frontend domain
- [ ] Set up email backend for notifications
- [ ] Enable HTTPS/SSL
- [ ] Configure static/media file storage (S3/CDN recommended)
- [ ] Set up logging and monitoring
- [ ] Use environment variables for secrets
- [ ] Test JWT token expiration flow

---

## 👨‍💻 Developer Notes

This project emphasizes:
- **Security First:** JWT tokens, role-based access, PIN verification
- **State Management:** Intelligent Auth/Me endpoint for clean frontend routing
- **Production Ready:** Query optimization, pagination, error handling
- **Scalability:** Async task processing ready, extensible architecture

---

## 📞 Support & Contribution

For issues, feature requests, or contributions:
1. Open an issue on GitHub
2. Create a feature branch
3. Submit a pull request with clear description
4. Ensure all tests pass

---

## 📄 License

This project is part of the Aidora humanitarian aid initiative.

*Built with ❤️ for humanitarian aid.*