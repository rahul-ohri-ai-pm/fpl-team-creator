/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        confidence: {
          high: '#10b981',    // green
          medium: '#f59e0b',  // yellow
          low: '#ef4444',     // red
        },
        fpl: {
          primary: '#3b82f6', // brand blue
          risk: '#f97316',    // orange
        }
      },
      fontSize: {
        'headline': ['20px', { lineHeight: '24px', fontWeight: '600' }],
        'subheading': ['16px', { lineHeight: '20px', fontWeight: '600' }],
        'body': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'caption': ['12px', { lineHeight: '16px', fontWeight: '400' }],
      },
    },
  },
  plugins: [],
}
