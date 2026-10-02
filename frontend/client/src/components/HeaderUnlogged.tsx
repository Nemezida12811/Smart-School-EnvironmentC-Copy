import './Header.css';
import logo from "../assets/logo2.png";
import login from "../assets/login.svg";

type HeaderLoggedProps = {
    onLogoClick?: () => void;
    onLoginClick?: () => void;
};

function HeaderLogged({ onLogoClick, onLoginClick }: HeaderLoggedProps) {

    return (
        <header className="header" >
            <div className="wrapper">
                <div className="logo">
                    <button onClick={onLogoClick} className="logo-link">
                        <img src={logo} alt="logo"/>
                    </button>
                </div>
                <div className="nav">
                    <button onClick={onLoginClick} className="login" >
                        <img src={login} alt="logout"/>
                        Log in
                    </button>
                </div>
            </div>
        </header>
    );
}

export default HeaderLogged;