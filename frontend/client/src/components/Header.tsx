import './Header.css';
import logo from "../assets/logo2.png";

type HeaderProps = {
    onLogoClick?: () => void;
};

function Header({ onLogoClick }: HeaderProps) {

    return (
        <header className="header" >
            <div className="wrapper">
                <div className="logo">
                    <button onClick={onLogoClick} className="logo-link">
                        <img src={logo} alt="logo"/>
                    </button>
                </div>
            </div>
        </header>
    );
}

export default Header;