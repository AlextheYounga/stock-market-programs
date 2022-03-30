// This is a minimal config.
// If you need the full config, get it from here:
// https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
module.exports = {
    purge: [
        // Templates within theme app (e.g. base.html)
        '../templates/**/*.html',
        // Templates in other apps. Uncomment the following line if it matches
        // your project structure or change it to match.
        // '../../templates/**/*.html',
    ],
    darkMode: false, // or 'media' or 'class'
    theme: {
        extend: {
            colors: {
                'old-gray': '#B8C2CC',
                'gold': '#F2D024',
                'dark-mode': '#212121',
                'dark-mode-light': '#34363a',
                'dark-mode-lighter': '#303030',
                'dark-mode-lightest': '#424242',
                'dark-mode-blue': '#3d4852',
                'off-white': '#e6e6e6',
                'off-gray': '#737373',
                'dark-opacity': 'rgba(19,19,19,0.30);',
                'gray-darkest-alpha': 'rgba(56,56,56,.25);',        
              },
        },
    },
    variants: {
        extend: {},
    },
    plugins: [],
}
