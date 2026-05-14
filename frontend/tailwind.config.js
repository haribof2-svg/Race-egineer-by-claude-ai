/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        // F1 palette
        f1: {
          bg:       '#0a0a0a',
          surface:  '#111111',
          card:     '#181818',
          border:   '#2a2a2a',
          gold:     '#e8b800',
          'gold-dim': '#a07d00',
          red:      '#e8001a',
          green:    '#00d787',
          blue:     '#00a0dc',
          purple:   '#9b00e8',
          muted:    '#666666',
          sub:      '#999999',
          text:     '#f0f0f0',
        },
      },
      fontFamily: {
        f1:   ['"Rajdhani"', 'monospace', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        '2xs': '0.625rem',
      },
    },
  },
  plugins: [],
};
