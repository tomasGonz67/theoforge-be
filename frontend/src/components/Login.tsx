import { useState } from "react";
import { login, setCookie } from "../api";

const Login = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
  
    const handleLogin = async (e: React.FormEvent) => {
      e.preventDefault();
      console.log("Sending login request:", { username, password });
  
      try {
        const data = await login(username, password);
        console.log("Login response:", data);
        await setCookie(data.access_token); // Send token to set HTTP-only cookie
        console.log("Check cookie creation:");
        console.log(document.cookie);
        setMessage("Login successful! Cookie set.");
      } catch (error) {
        console.error("Login failed:", error instanceof Error ? error.message : String(error));
        setMessage("Login failed.");
      }
    };
  
    return (
      <div>
        <h2>Login</h2>
        <form onSubmit={handleLogin}>
          <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button type="submit">Login</button>
        </form>
        <p>{message}</p>
      </div>
    );
  };

export default Login;
