import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './App.css'
import { AppRoutes } from './App'
import { BrowserRouter, RouterProvider } from 'react-router-dom'

const container = document.getElementById('root')
const root = createRoot(container as HTMLElement)

root.render(
  <StrictMode>
    <RouterProvider router={AppRoutes} />
  </StrictMode>,
)
