/**
 * Test data for the OrangeHRM login module.
 *
 * NOTE: OrangeHRM publishes these demo credentials directly on its public
 * login page, so they are safe to use for this demo environment.
 */
export const loginData = {
  validUser: {
    username: 'Admin',
    password: 'admin123',
  },
  invalidUser: {
    username: 'InvalidUser',
    password: 'WrongPass123',
  },
  emptyUser: {
    username: '',
    password: '',
  },
  messages: {
    invalidCredentials: 'Invalid credentials',
    required: 'Required',
  },
  urls: {
    login: '/web/index.php/auth/login',
    dashboard: '/web/index.php/dashboard/index',
  },
  title: {
    dashboard: 'Dashboard',
  },
} as const;

export type LoginData = typeof loginData;
