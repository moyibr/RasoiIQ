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
          base: '#14181F',
          surface: '#1B212B',
          raised: '#232B38',
        },
        accent: {
          primary: '#E8A33D',
          secondary: '#4FB5C7',
        },
        status: {
          success: '#5FAE6E',
          warning: '#E8A33D',
          critical: '#D9564A',
        },
        content: {
          primary: '#F2F0EA',
          secondary: '#9AA3B2',
        }
      }
    },
  },
  plugins: [],
}
export default config
