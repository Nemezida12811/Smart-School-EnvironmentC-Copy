import './buttons.css';
import backArrow from '../assets/back_arrow.svg';

type BackButtonProps = {
    text: string;
    onClick?: () => void;
    transparent?: boolean;
};

function BackButton({text, onClick, transparent}: BackButtonProps) {
    return (
        <div className="back">
            <div className="wrapper">
                <button onClick={onClick} className={`back-button ${transparent ? 'back-button--transparent' : ''}`}>
                    <img src={backArrow} alt="arrow"/>
                    {text}
                </button>
            </div>
        </div>
    );
}

export default BackButton;