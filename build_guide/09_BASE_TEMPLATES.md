# 09 — Base Templates & Login

> **Goal:** Build the master HTML layouts using Tailwind CSS (via CDN) and the Login page. 

---

## File 1 — `templates/base/base.html`

This is the main application layout containing the sidebar, top navigation, and message toasts.

```html
<!-- backend/templates/base/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Face Attendance{% endblock %}</title>
    
    <!-- Google Fonts: Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Phosphor Icons -->
    <script src="https://unpkg.com/@phosphor-icons/web"></script>

    <!-- Tailwind CSS (CDN for Development) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        primary: {
                            50: '#eff6ff',
                            100: '#dbeafe',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                        }
                    }
                }
            }
        }
    </script>
    
    <!-- Custom CSS for animations and tweaks -->
    <style>
        .glass-effect {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .toast-enter {
            animation: slideInRight 0.3s ease-out forwards;
        }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gray-50 text-gray-800 font-sans antialiased flex h-screen overflow-hidden">

    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col shadow-sm z-10">
        <!-- Logo Area -->
        <div class="h-16 flex items-center px-6 border-b border-gray-200">
            <i class="ph-fill ph-scan text-primary-600 text-3xl mr-3"></i>
            <span class="text-xl font-bold tracking-tight text-gray-900">FaceTrack</span>
        </div>

        <!-- Navigation Links -->
        <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
            
            {% if user_role == 'ADMIN' or user_role == 'TEACHER' %}
                <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-4">Overview</p>
                <a href="{% url 'dashboard' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-squares-four text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Dashboard
                </a>
                
                <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-6">Attendance</p>
                <a href="{% url 'attendance' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-calendar-check text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Daily Records
                </a>
                <a href="{% url 'report-daily' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-chart-bar text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Daily Report
                </a>
                <a href="{% url 'report-monthly' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-chart-line-up text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Monthly Report
                </a>
            {% endif %}

            {% if user_role == 'ADMIN' %}
                <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-6">Management</p>
                <a href="{% url 'users' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-users text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Students & Staff
                </a>
                <a href="{% url 'enroll' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-face-mask text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Face Enrollment
                </a>
                <a href="{% url 'kiosk' %}" target="_blank" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-device-tablet text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    Launch Kiosk Mode
                </a>
            {% endif %}

            {% if user_role == 'STUDENT' %}
                <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-4">Personal</p>
                <a href="{% url 'my-attendance' %}" class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors group">
                    <i class="ph ph-user-focus text-lg mr-3 text-gray-400 group-hover:text-primary-500"></i>
                    My Attendance
                </a>
            {% endif %}

        </nav>

        <!-- User Profile Area -->
        <div class="p-4 border-t border-gray-200">
            <div class="flex items-center w-full group">
                <div class="w-9 h-9 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold text-sm shrink-0">
                    {{ request.user.first_name|first|default:request.user.username|first|upper }}
                </div>
                <div class="ml-3 overflow-hidden">
                    <p class="text-sm font-medium text-gray-900 truncate">{{ request.user.get_full_name|default:request.user.username }}</p>
                    <p class="text-xs text-gray-500 truncate">{{ user_role|title }}</p>
                </div>
                <a href="{% url 'logout' %}" class="ml-auto text-gray-400 hover:text-red-500 transition-colors p-1" title="Logout">
                    <i class="ph ph-sign-out text-xl"></i>
                </a>
            </div>
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col h-screen overflow-hidden bg-gray-50/50 relative">
        
        <!-- Header (Mobile Trigger + Breadcrumbs) -->
        <header class="h-16 glass-effect flex items-center justify-between px-6 z-10">
            <div class="flex items-center">
                <h1 class="text-xl font-semibold text-gray-800">{% block header_title %}Overview{% endblock %}</h1>
            </div>
        </header>

        <!-- Messages / Toasts -->
        <div id="toast-container" class="fixed top-20 right-6 z-50 flex flex-col gap-3">
            {% if messages %}
                {% for message in messages %}
                    <div class="toast-enter flex items-center p-4 w-full max-w-sm bg-white rounded-lg shadow-lg border-l-4 
                        {% if message.tags == 'success' %}border-green-500 text-green-800
                        {% elif message.tags == 'error' %}border-red-500 text-red-800
                        {% elif message.tags == 'warning' %}border-yellow-500 text-yellow-800
                        {% else %}border-blue-500 text-blue-800{% endif %}" role="alert">
                        
                        <div class="ml-3 text-sm font-medium">{{ message }}</div>
                        <button type="button" class="ml-auto -mx-1.5 -my-1.5 bg-white text-gray-400 hover:text-gray-900 rounded-lg p-1.5 hover:bg-gray-100 inline-flex items-center justify-center h-8 w-8" onclick="this.parentElement.remove();">
                            <span class="sr-only">Close</span>
                            <i class="ph ph-x"></i>
                        </button>
                    </div>
                {% endfor %}
            {% endif %}
        </div>

        <!-- Scrollable Page Content -->
        <div class="flex-1 overflow-y-auto p-6">
            {% block content %}
            {% endblock %}
        </div>
    </main>

    {% block extra_scripts %}{% endblock %}
    <script>
        // Auto-hide toasts after 5 seconds
        setTimeout(() => {
            const toasts = document.querySelectorAll('#toast-container > div');
            toasts.forEach(toast => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                toast.style.transition = 'all 0.3s ease-out';
                setTimeout(() => toast.remove(), 300);
            });
        }, 5000);
    </script>
</body>
</html>
```

---

## File 2 — `templates/base/base_kiosk.html`

Used for the fullscreen kiosk check-in interface.

```html
<!-- backend/templates/base/base_kiosk.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FaceTrack Kiosk</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: white; }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex flex-col">
    {% block content %}{% endblock %}
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

---

## File 3 — `templates/accounts/login.html`

The modern, glassmorphic login page.

```html
<!-- backend/templates/accounts/login.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - FaceTrack</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'] },
                    colors: { primary: { 500: '#3b82f6', 600: '#2563eb' } }
                }
            }
        }
    </script>
    <style>
        .bg-pattern {
            background-image: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="bg-pattern min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
    
    <!-- Decorative background blobs -->
    <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary-600 rounded-full mix-blend-multiply filter blur-[100px] opacity-30 animate-blob"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-[100px] opacity-30 animate-blob animation-delay-2000"></div>

    <div class="w-full max-w-md glass-card rounded-2xl shadow-2xl p-8 relative z-10 text-white">
        
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-500/20 text-primary-400 mb-4 ring-1 ring-primary-500/30">
                <i class="ph-fill ph-scan text-3xl"></i>
            </div>
            <h2 class="text-3xl font-bold tracking-tight mb-2">FaceTrack</h2>
            <p class="text-slate-400 text-sm">Sign in to manage attendance and records</p>
        </div>

        {% if messages %}
            {% for message in messages %}
                <div class="mb-4 p-3 rounded-lg text-sm bg-red-500/10 border border-red-500/20 text-red-400 text-center">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}

        <form method="POST" action="{% url 'login' %}" class="space-y-5">
            {% csrf_token %}
            <div>
                <label for="username" class="block text-sm font-medium text-slate-300 mb-1.5">Username or Employee ID</label>
                <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <i class="ph ph-user"></i>
                    </div>
                    <input type="text" name="username" id="username" required
                        class="block w-full pl-10 px-4 py-2.5 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-shadow outline-none"
                        placeholder="e.g. teacher001">
                </div>
            </div>

            <div>
                <label for="password" class="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
                <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <i class="ph ph-lock-key"></i>
                    </div>
                    <input type="password" name="password" id="password" required
                        class="block w-full pl-10 px-4 py-2.5 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-shadow outline-none"
                        placeholder="••••••••">
                </div>
            </div>

            <button type="submit" class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-primary-500 transition-colors mt-2">
                Sign in
            </button>
        </form>
        
        <div class="mt-6 text-center text-xs text-slate-500">
            Powered by InsightFace & Django
        </div>
    </div>
</body>
</html>
```

---

**Next →** `10_DASHBOARD_TEMPLATES.md`
