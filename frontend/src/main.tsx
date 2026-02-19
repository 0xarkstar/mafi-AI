import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { Web3Provider } from './providers/Web3Provider'
import './styles/globals.css'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Root element not found')

createRoot(rootElement).render(
  <StrictMode>
    <Web3Provider>
      <App />
    </Web3Provider>
  </StrictMode>
)
