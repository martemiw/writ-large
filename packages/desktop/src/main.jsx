import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './App.css'

// No StrictMode — avoids double-invoking IPC calls in dev
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
