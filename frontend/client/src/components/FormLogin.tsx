import './forms.css';
import BigButton from "./BigButton.tsx";

type FormLoginProps = {
    email: string;
    setEmail: (val: string) => void;
    password: string;
    setPassword: (val: string) => void;
    onLoginClick: () => void;
    onSignupClick: () => void;
};

function FormLogin({ email, setEmail, password, setPassword, onLoginClick, onSignupClick }: FormLoginProps) {
    return (
        <div className="page">
            <div className="login-card">
                <h2 className="title">Have an account?</h2>

                <input
                    type="email"
                    placeholder="Email"
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

                <BigButton text="Log in" onClick={onLoginClick}/>

                <p onClick={onSignupClick} className="link">Create an account</p>
            </div>
        </div>
    );
}

export default FormLogin;