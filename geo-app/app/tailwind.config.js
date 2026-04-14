/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}"
  ],
  theme: {
    extend: {
      colors: {
        forest:    '#04202C',
        evergreen: '#304040',
        pine:      '#5B7065',
        fog:       '#C9D1C8',
        moss:      '#9EADA3',
        bark:      '#1A3036',
        midnight:  '#021519',
      },
      fontFamily: {
        display: ['Sora', 'sans-serif'],
        body:    ['DM Sans', 'system-ui', '-apple-system', 'sans-serif'],
        mono:    ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
    },
  },
  plugins: []
}
