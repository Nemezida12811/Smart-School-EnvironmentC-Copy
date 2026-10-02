import './forms.css';
import BigButton from "./BigButton.tsx";

type FormSignupProps = {
    username: string;
    setUsername: (val: string) => void;
    email: string;
    setEmail: (val: string) => void;
    password: string;
    setPassword: (val: string) => void;
    onSignupClick: () => void;
    onLoginClick: () => void;
};

function FormSignup({
                        username,
                        setUsername,
                        email,
                        setEmail,
                        password,
                        setPassword,
                        onSignupClick,
                        onLoginClick
                    }: FormSignupProps) {
    return (
        <div className="page">
            <div className="login-card">
                <h2 className="title">Create your account</h2>

                <input
                    type="text"
                    placeholder="Username"
                    className="input"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
                <input
                    type="email"
                    placeholder="Email address"
                    className="input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <input
                    type="password"
                    placeholder="Password"
                    className="input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />

                <BigButton text="Sign up" onClick={onSignupClick}/>

                <p onClick={onLoginClick} className="link">I already have an account</p>
            </div>
        </div>
    );
}

export default FormSignup;