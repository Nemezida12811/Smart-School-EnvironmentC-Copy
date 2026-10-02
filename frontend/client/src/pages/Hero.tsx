import "./hero.css";
import BigButton from "../components/BigButton.tsx";
import Footer from "../components/Footer.tsx";
import bgLogo from "../assets/big_logo.png";
import {useNavigate} from "react-router-dom";

function Hero() {
    const navigate = useNavigate();
    return (
        <div className="hero">
            {/* background logo */}
            <img src={bgLogo} alt="" className="hero-bg-logo" />

            <div className="hero-content">
                <h1 className="hero-title">Comfort Control</h1>

                <p className="hero-subtitle">
                    See every room&apos;s comfort index and make sure your students study
                    in the best environment
                </p>

                <div className="hero-actions">
                    <BigButton text="Log in" onClick={() => navigate('/login')} />
                    <button className="hero-link" onClick={() => navigate('/signup')}>Sign up</button>
                </div>

                <button className="hero-guest" onClick={() => navigate('/locations/new')}>Continue as Guest</button>
            </div>

            <Footer />
        </div>
    );
}

export default Hero;
