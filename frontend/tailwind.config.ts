import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
        display: ['var(--font-space-grotesk)', 'sans-serif'],
      },
      colors: {
        ink: {
          base: '#020617',
          surface: '#0F172A',
          raised: '#1E293B',
        },
        accent: {
          primary: '#10B981', // Vibrant Emerald
          secondary: '#F59E0B', // Bright Amber
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          critical: '#EF4444',
        },
        content: {
          primary: '#F8FAFC',
          secondary: '#94A3B8',
        }
      }
    },
  },
  plugins: [],
}
export default config
