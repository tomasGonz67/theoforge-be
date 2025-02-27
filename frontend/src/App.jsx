import './App.css'
import Dashboard from './components/Dashboard'
import Login from './components/Login'

function App() {

  return (
      <div className="card">
        <h1>FastAPI Auth Test</h1>
        <Login />
        <Dashboard />
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
  )
}

export default App
