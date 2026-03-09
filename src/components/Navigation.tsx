import { Link } from 'react-router-dom'

function Navigation() {
  return (
    <nav>
      <strong>The Sweet Tooth - Driver's App</strong>
      <div>
        <Link to="/">Dashboard</Link>
        <Link to="/deliveries">Deliveries</Link>
      </div>
    </nav>
  )
}

export default Navigation
