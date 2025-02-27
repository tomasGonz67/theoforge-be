import { useState } from "react";
import { checkAuth } from "../api";

const Dashboard = () => {
  const [authMessage, setAuthMessage] = useState("");

  const handleCheckAuth = async () => {
    try {
      const data = await checkAuth();
      console.log("Auth Response:", data); // Debugging: log the actual response
      setAuthMessage(`Authenticated as: ${data.access_token}`);
    } catch {
      setAuthMessage("Not authenticated.");
    }
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <button onClick={handleCheckAuth}>Check Authentication</button>
      <p>{authMessage}</p>
    </div>
  );
};

export default Dashboard;
