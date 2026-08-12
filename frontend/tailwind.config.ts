import type { Config } from 'tailwindcss';

// Design tokens — "field audit console" identity.
// Dark-mode-first (per project brief), an inspector's console rather than
// a marketing page: ink-navy surfaces, a signal-amber accent standing in
// for "flagged opportunity," and a circuit-teal accent for "healthy /
// audited" state. Fonts are system stacks on purpose (not Google Fonts):
// this is an offline-first PWA, so nothing in the shell should depend on
// a network fetch to render correctly — see globals.css for the rationale.
const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0F141B',
          50: '#F4F5F6',
          100: '#E4E7EA',
          200: '#C3C9D1',
          300: '#95A0AC',
          400: '#5B6472',
          500: '#3C4552',
          600: '#2B323D',
          700: '#1D232C',
          800: '#171D24',
          900: '#0F141B',
          950: '#0A0D12',
        },
        paper: {
          DEFAULT: '#F7F5F0',
          dim: '#EDEAE2',
        },
        signal: {
          DEFAULT: '#F2A93B',
          dim: '#B87F27',
          bright: '#FFC466',
        },
        circuit: {
          DEFAULT: '#3FBFAD',
          dim: '#2C8A7C',
          bright: '#68E0D0',
        },
        alert: {
          DEFAULT: '#E15A45',
          dim: '#A83F30',
        },
        // Semantic, theme-aware tokens: these read CSS custom properties
        // that flip value between the dark (default) and light themes in
        // globals.css, so components never need to hand-write dark:/light:
        // variants — one class works correctly in both themes.
        surface: 'var(--surface)',
        'surface-2': 'var(--surface-2)',
        edge: 'var(--edge)',
        fg: 'var(--fg)',
        'fg-muted': 'var(--fg-muted)',
        'fg-faint': 'var(--fg-faint)',
      },
      fontFamily: {
        display: [
          'Segoe UI',
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        body: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        data: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Consolas',
          'Liberation Mono',
          'monospace',
        ],
      },
      letterSpacing: {
        eyebrow: '0.18em',
      },
      boxShadow: {
        plate: '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 1px 2px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
};

export default config;
