import "./Log.css";
import Footer from "../components/Footer.tsx";
import Header from "../components/Header.tsx";
import BackButton from "../components/BackButton.tsx";
import FormLogin from "../components/FormLogin.tsx";
import {useNavigate} from "react-router-dom";
import {useState} from "react";
import {authApi} from "../newRestApiService.tsx";

function Login({ onLogin }: { onLogin: (user: any) => void }) {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const processLogin = async () => {
        if (!email.trim() || !password.trim()) {
            alert("Please enter both email and password");
            return;
        }

        try {
            const result = await authApi.login({
                email: email,
                password: password
            });
            localStorage.setItem('token', result.token);

            onLogin(result.user);

            navigate('/locations');

        } catch (error: any) {
            alert(error.message || "Login failed");
        }
    };

    return (
        <div className="content">
            <Header onLogoClick={() => navigate('/')}/>
            <BackButton text="Back" transparent onClick={() => navigate(-1)}/>
            <FormLogin
                email={email}
                setEmail={setEmail}
                password={password}
                setPassword={setPassword}
                onLoginClick={processLogin}
                onSignupClick={() => navigate('/signup')}
            />
            <Footer/>
        </div>
    );
}

export default Login;
