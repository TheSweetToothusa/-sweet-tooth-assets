function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <div className="card">
        <h3>Today's Summary</h3>
        <p>Pending deliveries: 0</p>
        <p>Completed deliveries: 0</p>
      </div>
      <div className="card">
        <h3>Quick Actions</h3>
        <p>No active deliveries. Check the Deliveries page for new assignments.</p>
      </div>
    </div>
  )
}

export default Dashboard
