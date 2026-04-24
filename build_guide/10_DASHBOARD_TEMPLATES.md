# 10 — Dashboard Templates

> **Goal:** Create the main dashboard template to display high-level metrics, recent check-ins, and attendance charts.

---

## File 1 — `templates/dashboard/index.html`

This template visualizes the system's current status and uses Chart.js for the weekly attendance graph.

```html
<!-- backend/templates/dashboard/index.html -->
{% extends 'base/base.html' %}

{% block title %}Dashboard - FaceTrack{% endblock %}
{% block header_title %}System Overview{% endblock %}

{% block extra_head %}
<!-- Chart.js for graphs -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% endblock %}

{% block content %}
<div class="space-y-6">
    
    <!-- Top Stats Row -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        <!-- Total Users Card -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center transition-transform hover:-translate-y-1 duration-300">
            <div class="w-12 h-12 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center text-2xl shrink-0">
                <i class="ph-fill ph-users"></i>
            </div>
            <div class="ml-4">
                <p class="text-sm font-medium text-gray-500">Total Users</p>
                <h3 class="text-2xl font-bold text-gray-900">{{ total_users }}</h3>
            </div>
        </div>

        <!-- Enrollment Rate Card -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center transition-transform hover:-translate-y-1 duration-300">
            <div class="w-12 h-12 rounded-full bg-indigo-50 text-indigo-500 flex items-center justify-center text-2xl shrink-0">
                <i class="ph-fill ph-face-mask"></i>
            </div>
            <div class="ml-4">
                <p class="text-sm font-medium text-gray-500">Enrolled</p>
                <div class="flex items-baseline">
                    <h3 class="text-2xl font-bold text-gray-900">{{ enrolled_users }}</h3>
                    <span class="ml-2 text-xs font-semibold text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded-full">{{ enrollment_rate }}%</span>
                </div>
            </div>
        </div>

        <!-- Today's Present Card -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center transition-transform hover:-translate-y-1 duration-300">
            <div class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-500 flex items-center justify-center text-2xl shrink-0">
                <i class="ph-fill ph-check-circle"></i>
            </div>
            <div class="ml-4">
                <p class="text-sm font-medium text-gray-500">Present Today</p>
                <div class="flex items-baseline">
                    <h3 class="text-2xl font-bold text-gray-900">{{ today_present }}</h3>
                    <span class="ml-2 text-xs font-semibold text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">{{ attendance_rate }}%</span>
                </div>
            </div>
        </div>

        <!-- Today's Absent Card -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center transition-transform hover:-translate-y-1 duration-300">
            <div class="w-12 h-12 rounded-full bg-red-50 text-red-500 flex items-center justify-center text-2xl shrink-0">
                <i class="ph-fill ph-x-circle"></i>
            </div>
            <div class="ml-4">
                <p class="text-sm font-medium text-gray-500">Absent Today</p>
                <h3 class="text-2xl font-bold text-gray-900">{{ today_absent }}</h3>
            </div>
        </div>
    </div>

    <!-- Middle Section: Chart & Departments -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Attendance Chart -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-2">
            <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <i class="ph ph-chart-line text-xl mr-2 text-primary-500"></i> Last 7 Days Attendance
            </h3>
            <div class="h-64">
                <canvas id="attendanceChart"></canvas>
            </div>
        </div>

        <!-- Department Breakdown -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <i class="ph ph-buildings text-xl mr-2 text-primary-500"></i> Department Stats
            </h3>
            <div class="space-y-4">
                {% for dept in dept_stats %}
                <div>
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-sm font-medium text-gray-700">{{ dept.name }}</span>
                        <span class="text-sm font-semibold text-gray-900">{{ dept.rate }}%</span>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-2">
                        <div class="bg-primary-500 h-2 rounded-full" style="width: {{ dept.rate }}%"></div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">{{ dept.present }} / {{ dept.total }} present</p>
                </div>
                {% empty %}
                <p class="text-sm text-gray-500 italic">No department data available.</p>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Recent Check-ins Table -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-6 border-b border-gray-100 flex justify-between items-center">
            <h3 class="text-lg font-bold text-gray-900 flex items-center">
                <i class="ph ph-clock-counter-clockwise text-xl mr-2 text-primary-500"></i> Recent Check-ins
            </h3>
            <a href="{% url 'attendance' %}" class="text-sm font-medium text-primary-600 hover:text-primary-700">View All</a>
        </div>
        
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                        <th class="px-6 py-3 font-medium">User</th>
                        <th class="px-6 py-3 font-medium">Department</th>
                        <th class="px-6 py-3 font-medium">Time</th>
                        <th class="px-6 py-3 font-medium">Mode</th>
                        <th class="px-6 py-3 font-medium">Status</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 text-sm">
                    {% for record in recent_checkins %}
                    <tr class="hover:bg-gray-50 transition-colors">
                        <td class="px-6 py-4">
                            <div class="flex items-center">
                                <div class="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center font-bold text-xs mr-3">
                                    {{ record.user.get_full_name|first|default:record.user.username|first|upper }}
                                </div>
                                <div>
                                    <p class="font-medium text-gray-900">{{ record.user.get_full_name }}</p>
                                    <p class="text-xs text-gray-500">{{ record.user.profile.employee_id }}</p>
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4 text-gray-600">{{ record.user.profile.department.name|default:"-" }}</td>
                        <td class="px-6 py-4 font-medium text-gray-900">{{ record.check_in_time|time:"H:i A" }}</td>
                        <td class="px-6 py-4">
                            <span class="text-xs text-gray-500">{{ record.get_attendance_mode_display }}</span>
                        </td>
                        <td class="px-6 py-4">
                            {% if record.status == 'PRESENT' %}
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Present
                            </span>
                            {% elif record.status == 'LATE' %}
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                Late
                            </span>
                            {% else %}
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                {{ record.status }}
                            </span>
                            {% endif %}
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                            <i class="ph ph-coffee text-3xl mb-2 text-gray-300"></i>
                            <p>No check-ins yet today.</p>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const ctx = document.getElementById('attendanceChart').getContext('2d');
        
        const labels = {{ chart_labels|safe }};
        const presentData = {{ chart_present|safe }};
        const absentData = {{ chart_absent|safe }};

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Present/Late',
                        data: presentData,
                        backgroundColor: '#3b82f6',
                        borderRadius: 4,
                    },
                    {
                        label: 'Absent',
                        data: absentData,
                        backgroundColor: '#e2e8f0',
                        borderRadius: 4,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { usePointStyle: true, boxWidth: 8 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { borderDash: [4, 4], color: '#f1f5f9' },
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    });
</script>
{% endblock %}
```

---

**Next →** `11_KIOSK_TEMPLATES.md`
