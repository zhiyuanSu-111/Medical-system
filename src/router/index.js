import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import { Capacitor } from '@capacitor/core'
import { getUser } from '../auth'
import Home from '../views/Home.vue'
import AIConsultation from '../views/AIConsultation.vue'
import Appointment from '../views/Appointment.vue'
import AppointmentSubDepartment from '../views/AppointmentSubDepartment.vue'
import AppointmentSpecialty from '../views/AppointmentSpecialty.vue'
import AppointmentDoctor from '../views/AppointmentDoctor.vue'
import NavigationPreview from '../views/NavigationPreview.vue'
import PatientManager from '../views/PatientManager.vue'
import AppointmentHistory from '../views/AppointmentHistory.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import DoctorSchedule from '../views/DoctorSchedule.vue'
import AdminPanel from '../views/AdminPanel.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { public: true } },
  { path: '/register', name: 'Register', component: Register, meta: { public: true } },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { roles: ['patient'] }
  },
  {
    path: '/ai-consultation',
    name: 'AIConsultation',
    component: AIConsultation,
    meta: { roles: ['patient'] }
  },
  {
    path: '/appointment',
    name: 'Appointment',
    component: Appointment,
    meta: { roles: ['patient'] }
  },
  {
    path: '/appointment/subdepartment',
    name: 'AppointmentSubDepartment',
    component: AppointmentSubDepartment,
    meta: { roles: ['patient'] }
  },
  {
    path: '/appointment/specialty',
    name: 'AppointmentSpecialty',
    component: AppointmentSpecialty,
    meta: { roles: ['patient'] }
  },
  {
    path: '/appointment/doctor',
    name: 'AppointmentDoctor',
    component: AppointmentDoctor,
    meta: { roles: ['patient'] }
  },
  {
    path: '/navigation-preview',
    name: 'NavigationPreview',
    component: NavigationPreview,
    meta: { roles: ['patient'] }
  },
  {
    path: '/patients',
    name: 'PatientManager',
    component: PatientManager,
    meta: { roles: ['patient'] }
  },
  {
    path: '/appointment-history',
    name: 'AppointmentHistory',
    component: AppointmentHistory,
    meta: { roles: ['patient'] }
  },
  {
    path: '/doctor/schedule',
    name: 'DoctorSchedule',
    component: DoctorSchedule,
    meta: { roles: ['doctor'] }
  },
  {
    path: '/admin',
    name: 'AdminPanel',
    component: AdminPanel,
    meta: { roles: ['admin'] }
  }
]

const router = createRouter({
  history: Capacitor.isNativePlatform() ? createWebHashHistory() : createWebHistory(),
  routes
})

function homeForRole(role) {
  if (role === 'admin') return '/admin'
  if (role === 'doctor') return '/doctor/schedule'
  return '/'
}

router.beforeEach((to, from, next) => {
  const user = getUser()
  const role = user && user.role

  if (to.meta.public) {
    if (user && (to.name === 'Login' || to.name === 'Register')) {
      return next(homeForRole(role))
    }
    return next()
  }

  const need = to.meta.roles
  if (!need || !need.length) {
    return next()
  }

  if (!user) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (!need.includes(role)) {
    return next(homeForRole(role))
  }

  next()
})

export default router
