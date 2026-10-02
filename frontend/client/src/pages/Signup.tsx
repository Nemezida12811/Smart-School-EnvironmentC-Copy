import "./Log.css";
import Footer from "../components/Footer.tsx";
import Header from "../components/Header.tsx";
import BackButton from "../components/BackButton.tsx";
import FormSignup from "../components/FormSignup.tsx";
import {useNavigate} from "react-router-dom";
import {useState} from "react";
import {authApi} from "../newRestApiService.tsx";


function Signup({ onSignup }: { onSignup: (user: any) => void }) {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleSignupAction = async () => {
        if (!username.trim() || !email.trim() || !password.trim()) {
            alert("Please fill in all fields.");
            return;
        }

        try {
            const result = await authApi.register({
                username,
                email,
                password
            });

            localStorage.setItem('token', result.token);

            onSignup(result.user);

            navigate('/locations');

        } catch (error: any) {
            alert(error.message || "Registration failed. Please try again.");
        }
    };

    return (
        <div className="content">
            <Header onLogoClick={() => navigate('/')}/>
            <BackButton text="Back" transparent onClick={() => navigate(-1)} />
            <FormSignup
                username={username}
                setUsername={setUsername}
                email={email}
                setEmail={setEmail}
                password={password}
                setPassword={setPassword}
                onSignupClick={handleSignupAction}
                onLoginClick={() => navigate('/login')}
            />
            <Footer/>
        </div>
    );
}

export default Signup;
