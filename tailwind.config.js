/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: "class",
    content: [
        "./templates/**/*.html",
        "./static/**/*.js"
    ],
    theme: {
        extend: {
            colors: {
                primary: "#4F46E5",
                secondary: "#6366F1",
                "background-light": "#F8FAFC",
                "background-dark": "#0F172A",
            },
            fontFamily: {
                display: ["Plus Jakarta Sans", "sans-serif"],
                body: ["Inter", "sans-serif"],
            },
            borderRadius: {
                DEFAULT: "16px",
                "2xl": "16px",
                "3xl": "24px",
            },
            boxShadow: {
                'glass': '0 10px 40px -10px rgba(0,0,0,0.08)',
                'glass-hover': '0 20px 40px -10px rgba(79, 70, 229, 0.15)',
            },
            animation: {
                'blob': 'blob 7s infinite',
                'slide-up': 'slideUp 0.5s ease-out forwards',
                'ping-slow': 'ping 3s cubic-bezier(0, 0, 0.2, 1) infinite',
            },
            keyframes: {
                blob: {
                    '0%': { transform: 'translate(0px, 0px) scale(1)' },
                    '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
                    '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
                    '100%': { transform: 'translate(0px, 0px) scale(1)' }
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' }
                },
                'bounce-subtle': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-4px)' }
                }
            }
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/container-queries')
    ],
};
