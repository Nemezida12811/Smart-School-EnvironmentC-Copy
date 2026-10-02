import './Header.css';
import logo from "../assets/logo2.png";
import logout from "../assets/logout.svg";
import {useNavigate} from "react-router-dom";

type HeaderLoggedProps = {
    username: string;
    onLogoClick?: () => void;
    onLogout: () => void
};

function HeaderLogged({ username, onLogoClick, onLogout }: HeaderLoggedProps) {
    const navigate = useNavigate();

    const fullyLogout = () => {
        onLogout();
        navigate('/');
    };

    return (
        <header className="header" >
            <div className="wrapper">
                <div className="logo">
                    <button onClick={onLogoClick} className="logo-link">
                        <img src={logo} alt="logo"/>
                    </button>
                </div>
                <div className="nav">
                    <div className="username"> {username}</div>
                    <button onClick={fullyLogout} className="logout" >
                        <img src={logout} alt="logout"/>
                        Log out
                    </button>
                </div>
            </div>
        </header>
    );
}

export default HeaderLogged;