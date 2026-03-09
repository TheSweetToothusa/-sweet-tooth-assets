import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Deliveries from './pages/Deliveries'
import Navigation from './components/Navigation'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/deliveries" element={<Deliveries />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
