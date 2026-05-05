import React, {useState} from 'react';

export default function LoginPage({profile, handleProfileChange, createUser, loginAs}){
  const [loginId, setLoginId] = useState('');
  return (
    <div className="center-card">
      <h2>Welcome to GigShield</h2>
      <p>Please login with your user id or create a new demo user.</p>
      <div className="form-row">
        <input placeholder="Existing user id" value={loginId} onChange={(e)=>setLoginId(e.target.value)} />
        <button onClick={()=>loginAs(Number(loginId))} disabled={!loginId}>Login</button>
      </div>
      <div className="divider">or</div>
      <div>
        <h3>Create demo user</h3>
        <div className="form-row">
          <input name="name" value={profile.name} onChange={handleProfileChange} placeholder="Name" />
          <select name="language" value={profile.language} onChange={handleProfileChange}>
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="kannada">Kannada</option>
          </select>
          <button onClick={createUser}>Create</button>
        </div>
      </div>
    </div>
  );
}
